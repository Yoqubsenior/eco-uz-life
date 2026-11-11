"""Safe processing of user-uploaded photos.

Never trust an upload: not its name, not its extension, not its Content-Type header.
Every photo is decoded by Pillow and RE-ENCODED as a fresh JPEG. That:

- rejects anything that isn't really an image (a .php or .html renamed to .jpg);
- drops hidden payloads appended to the file (polyglot files);
- strips ALL metadata, including EXIF GPS (the photographer's exact home location),
  camera serial number and timestamps;
- normalises size, so a 50 MB photo doesn't fill the disk or the user's mobile data.
"""

from dataclasses import dataclass
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SIDE_PX = 1600
MAX_SOURCE_PIXELS = 40_000_000  # decompression-bomb guard: a tiny file can decode to GBs of RAM
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
JPEG_QUALITY = 85


class InvalidImage(ValueError):
    """The upload is not an acceptable image. The message is safe to show to the user."""


@dataclass(frozen=True)
class ProcessedImage:
    content: ContentFile
    width: int
    height: int


def process_image(upload) -> ProcessedImage:
    if upload.size > MAX_UPLOAD_BYTES:
        raise InvalidImage("Rasm hajmi 5 MB dan oshmasligi kerak.")

    try:
        upload.seek(0)
        with Image.open(upload) as probe:
            # Check type and size from the header BEFORE decoding pixels.
            if probe.format not in ALLOWED_FORMATS:
                raise InvalidImage("Faqat JPEG, PNG yoki WEBP rasmlar qabul qilinadi.")
            if probe.width * probe.height > MAX_SOURCE_PIXELS:
                raise InvalidImage("Rasm o'lchami juda katta.")
            probe.verify()  # structural integrity check; the object is unusable afterwards

        upload.seek(0)
        with Image.open(upload) as img:
            # Apply the EXIF orientation first, otherwise phone photos end up sideways
            # once the EXIF data (which carried the rotation) is removed.
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")  # drops alpha / palette; JPEG has neither
            img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))  # keeps aspect ratio, never upscales

            buffer = BytesIO()
            # No `exif=` argument -> the new file carries no metadata at all.
            img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            width, height = img.size
    except InvalidImage:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise InvalidImage("Fayl haqiqiy rasm emas yoki buzilgan.") from exc

    return ProcessedImage(content=ContentFile(buffer.getvalue()), width=width, height=height)
