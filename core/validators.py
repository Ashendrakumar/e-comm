"""Reusable upload validators (Module 11 — media management)."""
import os
from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}


def validate_image_file(value):
    """Reject oversized files and non-image extensions on ImageField uploads."""
    # Size check (skip if the file isn't newly uploaded / has no size attr)
    size = getattr(value, 'size', None)
    if size and size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f'Image too large — maximum size is {MAX_IMAGE_SIZE_MB} MB '
            f'(this file is {size / (1024 * 1024):.1f} MB).'
        )
    # Extension check
    ext = os.path.splitext(value.name)[1].lower()
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'Unsupported file type "{ext}". '
            f'Allowed: {", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))}.'
        )
