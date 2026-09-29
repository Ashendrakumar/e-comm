import io
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
            'name': 'Jane', 'email': 'jane@example.com', 'phone': '+91 98765 43210',
            'subject': 'Hello', 'message': 'Need a quote', 'inquiry_type': 'general',
        })
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(ContactInquiry.objects.filter(email='jane@example.com').count(), 1)

    def test_newsletter_subscribe(self):
        self.client.post(reverse('core:newsletter_subscribe'), {'email': 'sub@example.com'})
        self.assertTrue(NewsletterSubscription.objects.filter(email='sub@example.com').exists())

    def test_newsletter_resubscribe_is_not_an_error(self):
        NewsletterSubscription.objects.create(email='back@example.com', is_active=False)
        resp = self.client.post(reverse('core:newsletter_subscribe'), {'email': 'back@example.com'},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.json(), {'success': True, 'message': 'You are already subscribed!'})
        self.assertTrue(NewsletterSubscription.objects.get(email='back@example.com').is_active)

    def test_invalid_contact_returns_field_errors(self):
        resp = self.client.post(reverse('core:contact_submit'), {
            'name': 'J', 'email': 'not-an-email', 'phone': '12ab', 'subject': 'Hello',
            'message': 'Too short', 'inquiry_type': 'general',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        errors = resp.json()['errors']
        self.assertEqual(set(errors), {'name', 'email', 'phone', 'message'})
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_forms_render_the_client_side_rules(self):
        html = self.client.get(reverse('core:contact')).content.decode()
        self.assertIn('data-validate', html)
        self.assertRegex(html, r'<input type="tel" name="phone"[^>]*maxlength="20"')
        self.assertRegex(html, r'<textarea name="message"[^>]*minlength="10"')
        self.assertRegex(html, r'<textarea name="message"[^>]*maxlength="2000"')
        self.assertIn('js/form-validate.js', html)


class ValidatorTests(TestCase):
    class _Fake:
        def __init__(self, name, size):
            self.name, self.size = name, size

    def test_rejects_large_file(self):
        with self.assertRaises(ValidationError):
            validate_image_file(self._Fake('big.jpg', 10 * 1024 * 1024))

    def test_phone_numbers(self):
        from .validators import validate_phone
        for ok in ('', '+91 98765 43210', '(022) 2345-6789', '9876543210'):
            validate_phone(ok)
        for bad in ('12345', '98765abc10', '+91 98765 43210 12345 6'):
            with self.assertRaises(ValidationError, msg=bad):
                validate_phone(bad)

    def test_rejects_bad_extension(self):
        with self.assertRaises(ValidationError):
            validate_image_file(self._Fake('virus.exe', 1000))

    def test_accepts_valid_image(self):
        validate_image_file(self._Fake('photo.jpg', 1000))  # should not raise


from django.test import override_settings


@override_settings(DEBUG=True)
class FriendlyDebug404Tests(TestCase):
    def test_unknown_url_shows_site_404_in_debug(self):
        resp = self.client.get('/definitely-not-a-page/')
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, '404.html')

    def test_api_404_stays_json(self):
        resp = self.client.get('/api/v1/products/no-such-product/')
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))

    @override_settings(SHOW_TECHNICAL_404=True)
    def test_opt_out_keeps_django_debug_page(self):
        resp = self.client.get('/definitely-not-a-page/')
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateNotUsed(resp, '404.html')



# ── Production hardening ─────────────────────────────────────────────────────
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from .ratelimit import HONEYPOT_FIELD, client_ip, parse_rate


class RateLimitTests(TestCase):
    payload = {'name': 'Asha', 'email': 'asha@example.com', 'phone': '+91 98765 43210', 'subject': 'Hi',
               'message': 'Need a quote', 'inquiry_type': 'general'}

    def setUp(self):
        cache.clear()

    def test_parse_rate(self):
        self.assertEqual(parse_rate('10/10m'), (10, 600))
        self.assertEqual(parse_rate('5/h'), (5, 3600))
        with self.assertRaises(ValueError):
            parse_rate('lots')

    @override_settings(RATELIMIT_ENABLED=True, RATELIMIT_FORMS='2/10m')
    def test_contact_form_is_rate_limited(self):
        url = reverse('core:contact_submit')
        ajax = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        for _ in range(2):
            self.assertEqual(self.client.post(url, self.payload, **ajax).status_code, 200)
        resp = self.client.post(url, self.payload, **ajax)
        self.assertEqual(resp.status_code, 429)
        self.assertFalse(resp.json()['success'])
        self.assertEqual(ContactInquiry.objects.count(), 2)

    def test_honeypot_fakes_success_and_saves_nothing(self):
        resp = self.client.post(reverse('core:contact_submit'), {**self.payload, HONEYPOT_FIELD: 'http://spam'},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(resp.json()['success'])
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_honeypot_field_is_rendered_in_public_forms(self):
        self.assertContains(self.client.get(reverse('core:contact')), f'name="{HONEYPOT_FIELD}"')

    def test_client_ip_behind_proxy(self):
        rf = RequestFactory()
        req = rf.get('/', REMOTE_ADDR='10.0.0.2', HTTP_X_FORWARDED_FOR='6.6.6.6, 203.0.113.9')
        with override_settings(TRUSTED_PROXY_COUNT=0):
            self.assertEqual(client_ip(req), '10.0.0.2')
        with override_settings(TRUSTED_PROXY_COUNT=1):         # the forged left entry is ignored
            self.assertEqual(client_ip(req), '203.0.113.9')

    @override_settings(RATELIMIT_ENABLED=True, RATELIMIT_LOGIN='1/15m')
    def test_admin_login_locks_out(self):
        from django.conf import settings
        url = '/' + settings.ADMIN_URL + 'login/'
        self.client.post(url, {'username': 'x', 'password': 'y'})
        self.assertEqual(self.client.post(url, {'username': 'x', 'password': 'y'}).status_code, 429)


class OpsEndpointTests(TestCase):
    def test_healthz(self):
        resp = self.client.get('/healthz/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'status': 'ok'})

    def test_robots_does_not_reveal_admin(self):
        self.assertNotContains(self.client.get('/robots.txt'), 'admin')

    @override_settings(CSP_ENABLED=True, DEBUG=False)
    def test_csp_header_sent(self):
        resp = self.client.get(reverse('core:homepage'))
        self.assertIn("default-src 'self'", resp['Content-Security-Policy'])
        self.assertIn("object-src 'none'", resp['Content-Security-Policy'])


class SyncSiteCommandTests(TestCase):
    def test_sets_domain_and_strips_scheme(self):
        from django.contrib.sites.models import Site
        from django.core.management import call_command
        call_command('sync_site', domain='https://shop.example.in/', name='Shop', stdout=io.StringIO())
        self.assertEqual(Site.objects.get_current().domain, 'shop.example.in')
