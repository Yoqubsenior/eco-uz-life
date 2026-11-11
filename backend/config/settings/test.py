from .base import *  # noqa: F403

DEBUG = False

# Argon2 is deliberately slow. In tests that only slows the suite down, so use a fast hasher.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
