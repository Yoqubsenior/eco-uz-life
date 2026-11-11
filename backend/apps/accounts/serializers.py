from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .managers import normalize_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    # write_only: the password is accepted on input but never appears in any response.
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "password")
        read_only_fields = ("id",)
        # Drop the auto-generated case-SENSITIVE unique check; validate_email does it properly.
        extra_kwargs = {"email": {"validators": []}}

    def validate_email(self, value: str) -> str:
        email = normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def validate(self, attrs: dict) -> dict:
        # Run Django's password validators (length, common passwords, similarity to email...).
        # It lives in validate(), not validate_password(), because the similarity check needs
        # the email/name too. A temporary unsaved user carries them.
        candidate = User(email=attrs["email"], display_name=attrs.get("display_name", ""))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            # Attach errors to the "password" field (not non_field_errors),
            # so the app can show them under the password input.
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data: dict):
        return User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "display_name", "date_joined")
        # Email change needs re-verification — a separate, later feature.
        read_only_fields = ("id", "email", "date_joined")
