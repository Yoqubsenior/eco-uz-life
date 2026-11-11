from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import SECRET_KEY

DEBUG = False

# JWTs are signed with SECRET_KEY (HMAC-SHA256). A short key can be brute-forced,
# and whoever knows it can forge a token for any user. Refuse to start with a weak key.
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("change-me"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is too weak for production (min 50 chars).")

# Behind a reverse proxy that terminates HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # start with 30 days; raise once HTTPS is confirmed stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
