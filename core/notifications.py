"""Email the shop owner about new enquiries.

Recipient: Site Settings -> notification email, else the contact email, else
settings.DEFAULT_FROM_EMAIL. Always best-effort: a mail failure must never stop
an enquiry from being saved (it is already in the admin either way).
Development uses the console backend, so these print in the runserver terminal.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def staff_recipients():
    from .models import SiteSettings
    s = SiteSettings.get_settings()
    to = (s.notification_email or s.email or settings.DEFAULT_FROM_EMAIL or '').strip()
    return [to] if to else []


def notify_staff(subject, message, reply_to=None):
    """Send one enquiry notification. Returns True if the backend accepted it."""
    recipients = staff_recipients()
    if not recipients:
        return False
    try:
        from django.core.mail import EmailMessage
        EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL,
                     to=recipients, reply_to=[reply_to] if reply_to else None).send(fail_silently=False)
        return True
    except Exception:                       # never block the customer on email problems
        log.exception('Enquiry notification failed: %s', subject)
        return False
