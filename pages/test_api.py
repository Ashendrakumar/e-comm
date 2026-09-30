"""Mobile-app API: services, serving areas, FAQs, CMS pages."""
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .models import FAQCategory, FlatPage, GeneralFAQ, Service, ServiceFeature, ServiceInquiry, ServingArea


class PagesApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_services_and_inquiry(self):
        svc = Service.objects.create(title='TV Installation', short_description='Wall mounting')
        ServiceFeature.objects.create(service=svc, title='Same-day visit')
        Service.objects.create(title='Hidden', short_description='x', is_active=False)
        self.assertEqual([s['slug'] for s in self.client.get('/api/v1/services/').json()], ['tv-installation'])
        detail = self.client.get('/api/v1/services/tv-installation/').json()
        self.assertEqual(detail['features'][0]['title'], 'Same-day visit')

        resp = self.client.post('/api/v1/services/tv-installation/inquiry/', {
            'name': 'Meera', 'email': 'meera@example.com', 'city': 'Surat',
            'message': 'Please mount a 55 inch TV.'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ServiceInquiry.objects.get().service, svc)
        self.assertEqual(len(mail.outbox), 1)

    def test_serving_areas_and_pincode_check(self):
        ServingArea.objects.create(city='Surat', pincodes='395001, 395007')
        ServingArea.objects.create(city='Anand', pincodes='3950071')      # contains the digits, not the pincode
        detail = self.client.get('/api/v1/serving-areas/surat/').json()
        self.assertEqual(detail['pincodes'], ['395001', '395007'])
        self.assertIn('available_services', detail)

        hit = self.client.get('/api/v1/serving-areas/check/?pincode=395007').json()
        self.assertTrue(hit['serviceable'])
        self.assertEqual([a['city'] for a in hit['areas']], ['Surat'])
        self.assertFalse(self.client.get('/api/v1/serving-areas/check/?pincode=110001').json()['serviceable'])
        self.assertEqual(self.client.get('/api/v1/serving-areas/check/?pincode=12').status_code, 400)

    def test_faqs_grouped(self):
        cat = FAQCategory.objects.create(name='Delivery')
        GeneralFAQ.objects.create(category=cat, question='How fast?', answer='2 days')
        GeneralFAQ.objects.create(question='Open Sunday?', answer='No')
        FAQCategory.objects.create(name='Empty')
        groups = self.client.get('/api/v1/faqs/').json()
        self.assertEqual([(g['name'], len(g['faqs'])) for g in groups], [('Delivery', 1), ('General', 1)])

    def test_flat_pages(self):
        FlatPage.objects.create(title='Terms', content='<p>Be nice</p>')
        self.assertNotIn('content', self.client.get('/api/v1/pages/').json()[0])
        self.assertEqual(self.client.get('/api/v1/pages/terms/').json()['content'], '<p>Be nice</p>')
