from django.test import TestCase
from django.urls import reverse
from .models import Service, ServingArea, FlatPage


class PagesTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(title='Device Repair', short_description='Fast repairs')
        self.area = ServingArea.objects.create(city='Ahmedabad')
        self.page = FlatPage.objects.create(title='About Us', content='<p>Hello</p>')

    def test_slugs_autoset(self):
        self.assertEqual(self.service.slug, 'device-repair')
        self.assertEqual(self.area.slug, 'ahmedabad')
        self.assertEqual(self.page.slug, 'about-us')

    def test_services_list(self):
        resp = self.client.get(reverse('pages:services'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Device Repair')

    def test_service_detail(self):
        resp = self.client.get(self.service.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    def test_serving_areas(self):
        resp = self.client.get(reverse('pages:serving_areas'))
        self.assertEqual(resp.status_code, 200)

    def test_area_detail(self):
        resp = self.client.get(self.area.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    def test_flatpage(self):
        resp = self.client.get(self.page.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Hello')
