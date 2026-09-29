"""Email the shop owner about new enquiries.

Recipient: Site Settings -> notification email, else the contact email, else
settings.DEFAULT_FROM_EMAIL. Always best-effort: a mail failure must never stop
an enquiry from being saved (it is already in the admin either way).
Development uses the console backend, so these print in the runserver terminal.

Sent from a short-lived background thread (settings.NOTIFY_ASYNC) so the
visitor never waits on the SMTP server; EMAIL_TIMEOUT bounds a hung server.
"""
import logging
import threading

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection

log = logging.getLogger(__name__)


def staff_recipients():
    from .models import SiteSettings
    s = SiteSettings.get_settings()
    to = (s.notification_email or s.email or settings.DEFAULT_FROM_EMAIL or '').strip()
    return [to] if to else []


def _send(email):
    try:
        email.send(fail_silently=False)
        return True
    except Exception:                       # never block the customer on email problems
        log.exception('Enquiry notification failed: %s', email.subject)
        return False


def _send_in_background(email):
    try:
        _send(email)
    finally:
        connection.close()                  # the thread may have opened its own DB connection


def notify_staff(subject, message, reply_to=None):
    """Queue one enquiry notification. Returns True if it was sent / handed off."""
    recipients = staff_recipients()
    if not recipients:
        return False
    email = EmailMessage(subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL,
                         to=recipients, reply_to=[reply_to] if reply_to else None)
    if getattr(settings, 'NOTIFY_ASYNC', False):
        threading.Thread(target=_send_in_background, args=(email,), daemon=True,
                         name='notify-staff').start()
        return True
    return _send(email)
