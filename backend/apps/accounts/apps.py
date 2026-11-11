from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    label = "accounts"  # AUTH_USER_MODEL = "accounts.User" refers to this label
