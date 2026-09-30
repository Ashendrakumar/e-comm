"""Mobile-app API: home feed, config, banners, contact, newsletter."""
from decimal import Decimal

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from pages.models import FlatPage
from products.models import Category, Product
from .models import ContactInquiry, NewsletterSubscription, SiteSettings, SocialLink


class SiteApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_home_sections(self):
        cat = Category.objects.create(name='Audio', is_featured=True)
        old = Product.objects.create(name='Old Speaker', category=cat, price=Decimal('50'), is_featured=True)
        new = Product.objects.create(name='New Speaker', category=cat, price=Decimal('90'), is_featured=True,
                                     sale_price=Decimal('80'), stock=3)
        body = self.client.get('/api/v1/home/').json()
        for key in ('hero_banners', 'promo_banners', 'featured_categories', 'featured_brands',
                    'featured_products', 'trending_products', 'new_arrivals', 'deals', 'services',
                    'serving_areas', 'testimonials', 'why_choose_us'):
            self.assertIn(key, body)
        self.assertEqual([p['slug'] for p in body['featured_products']], [new.slug, old.slug])   # newest first
        self.assertEqual([p['slug'] for p in body['deals']], [new.slug])
        self.assertEqual(body['featured_categories'][0]['slug'], 'audio')

    def test_config_exposes_public_details_only(self):
        s = SiteSettings.get_settings()
        s.phone, s.notification_email = '+91 90000 00000', 'secret-inbox@example.com'
        s.save()
        SocialLink.objects.create(platform='instagram', url='https://instagram.com/tz')
        FlatPage.objects.create(title='Privacy Policy', content='...')
        resp = self.client.get('/api/v1/config/')
        body = resp.json()
        self.assertEqual(body['store']['phone'], '+91 90000 00000')
        self.assertNotContains(resp, 'secret-inbox')
        self.assertEqual(body['social_links'][0]['label'], 'Instagram')
        self.assertEqual(body['pages'][0]['slug'], 'privacy-policy')
        self.assertIn({'value': 'refurbished', 'label': 'Refurbished'}, body['choices']['product_condition'])

    def test_contact_saves_and_notifies(self):
        resp = self.client.post('/api/v1/contact/', {
            'name': 'Ravi', 'email': 'ravi@example.com', 'subject': 'Bulk order',
            'message': 'Need 20 laptops for an office.', 'inquiry_type': 'bulk'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ContactInquiry.objects.get().inquiry_type, 'bulk')
        self.assertEqual(len(mail.outbox), 1)

    def test_contact_validation(self):
        resp = self.client.post('/api/v1/contact/', {'name': 'Ravi'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('message', resp.json())

    def test_newsletter(self):
        self.assertEqual(self.client.post('/api/v1/newsletter/', {'email': 'a@example.com'}).status_code, 201)
        self.assertEqual(self.client.post('/api/v1/newsletter/', {'email': 'a@example.com'}).status_code, 200)
        self.assertEqual(self.client.post('/api/v1/newsletter/', {'email': 'nope'}).status_code, 400)
        self.assertEqual(NewsletterSubscription.objects.count(), 1)
