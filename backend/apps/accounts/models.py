from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from .managers import UserManager, normalize_email


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user: logs in with email, no username.

    Owning the model from day one means it can grow with ordinary migrations —
    `district` was added in Stage 5 exactly that way.
    """

    email = models.EmailField(max_length=254, unique=True)
    display_name = models.CharField(max_length=60, blank=True)
    # Home district: used for the district leaderboard. String reference avoids a circular import.
    district = models.ForeignKey(
        "geo.District", on_delete=models.SET_NULL, null=True, blank=True, related_name="residents"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # asked by createsuperuser besides email + password

    class Meta:
        constraints = [
            # Database-level guarantee, even for code paths that skip save() (bulk_create, raw SQL).
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        super().save(*args, **kwargs)
