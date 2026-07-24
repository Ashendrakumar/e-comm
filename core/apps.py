from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Python 3.14 compatibility for Django 4.2's template-context copy
        # (otherwise every admin changelist page raises a 500).
        from .compat import apply_template_context_copy_patch
        apply_template_context_copy_patch()
