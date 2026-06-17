from django.test import TestCase
from django.urls import reverse
from .models import ContactInquiry, NewsletterSubscription
from .validators import validate_image_file
from django.core.exceptions import ValidationError


class HomepageTests(TestCase):
    def test_homepage_loads(self):
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)

    def test_robots_and_sitemap(self):
        self.assertEqual(self.client.get('/robots.txt').status_code, 200)
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)


class ContactTests(TestCase):
    def test_contact_submit_creates_inquiry(self):
        resp = self.client.post(reverse('core:contact_submit'), {
            'name': 'Jane', 'email': 'jane@example.com', 'phone': '12345',
            'subject': 'Hello', 'message': 'Need a quote', 'inquiry_type': 'general',
        })
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(ContactInquiry.objects.filter(email='jane@example.com').count(), 1)

    def test_newsletter_subscribe(self):
        self.client.post(reverse('core:newsletter_subscribe'), {'email': 'sub@example.com'})
        self.assertTrue(NewsletterSubscription.objects.filter(email='sub@example.com').exists())


class ValidatorTests(TestCase):
    class _Fake:
        def __init__(self, name, size):
            self.name, self.size = name, size

    def test_rejects_large_file(self):
        with self.assertRaises(ValidationError):
            validate_image_file(self._Fake('big.jpg', 10 * 1024 * 1024))

    def test_rejects_bad_extension(self):
        with self.assertRaises(ValidationError):
            validate_image_file(self._Fake('virus.exe', 1000))

    def test_accepts_valid_image(self):
        validate_image_file(self._Fake('photo.jpg', 1000))  # should not raise
