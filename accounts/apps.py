from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Customer accounts for the mobile app: token sign-up / sign-in over the API."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
