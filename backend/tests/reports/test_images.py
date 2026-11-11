from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.reports.images import MAX_UPLOAD_BYTES, InvalidImage, process_image
from tests.reports.conftest import make_upload

ORIENTATION, MAKE, MODEL, DATETIME = 0x0112, 0x010F, 0x0110, 0x0132


def open_result(processed) -> Image.Image:
    return Image.open(BytesIO(processed.content.read()))


def test_large_photo_is_resized_and_reencoded_as_jpeg():
    processed = process_image(make_upload(size=(3000, 1500)))

    result = open_result(processed)
    assert result.format == "JPEG"
    assert result.size == (1600, 800)  # aspect ratio kept
    assert (processed.width, processed.height) == (1600, 800)


def test_all_exif_metadata_is_removed():
    exif = Image.Exif()
    exif[MAKE] = "PhoneMaker"
    exif[MODEL] = "Model X, serial 123456"
    exif[DATETIME] = "2026:11:11 20:00:00"

    result = open_result(process_image(make_upload(exif=exif)))

    assert len(result.getexif()) == 0


def test_exif_orientation_is_applied_before_stripping():
    # Phones store portrait photos as landscape + "rotate 90°" in EXIF.
    exif = Image.Exif()
    exif[ORIENTATION] = 6

    result = open_result(process_image(make_upload(size=(200, 100), exif=exif)))

    assert result.size == (100, 200)  # rotated into place, not left sideways


def test_png_with_transparency_is_accepted_and_converted():
    result = open_result(process_image(make_upload(fmt="PNG", mode="RGBA", name="p.png")))

    assert result.format == "JPEG"
    assert result.mode == "RGB"


def test_non_image_with_jpg_extension_is_rejected():
    fake = SimpleUploadedFile("photo.jpg", b"<?php system($_GET['c']); ?>", "image/jpeg")

    with pytest.raises(InvalidImage):
        process_image(fake)


def test_unsupported_format_is_rejected():
    with pytest.raises(InvalidImage, match="JPEG, PNG"):
        process_image(make_upload(fmt="GIF", mode="P", name="a.gif"))


def test_too_big_file_is_rejected_before_decoding():
    huge = SimpleUploadedFile("big.jpg", b"0" * (MAX_UPLOAD_BYTES + 1), "image/jpeg")

    with pytest.raises(InvalidImage, match="5 MB"):
        process_image(huge)
