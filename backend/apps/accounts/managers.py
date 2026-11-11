from django.contrib.auth.base_user import BaseUserManager


def normalize_email(email: str) -> str:
    """Lowercase the whole address.

    Django's BaseUserManager.normalize_email lowercases only the domain part. In practice
    nobody expects Ali@mail.uz and ali@mail.uz to be different people, so we lowercase all of it.
    """
    return email.strip().lower()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=normalize_email(email), **extra_fields)
        user.set_password(password)  # None -> unusable password, never stored in plain text
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username: str):
        # Used by the login backend: "ALI@Mail.uz" must log in as "ali@mail.uz".
        return self.get(email=normalize_email(username))
