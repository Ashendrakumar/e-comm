from django.test import TestCase
from django.urls import reverse
from .models import Service, ServingArea, FlatPage, ServiceAvailability


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


class ServiceAvailabilityApiTests(TestCase):
    url = '/api/v1/service-availability/'

    def setUp(self):
        ServiceAvailability.objects.all().delete()          # drop the seeded rows
        self.delivery = ServiceAvailability.objects.create(title='Doorstep Delivery', icon='ti-truck', order=0)
        self.repair   = ServiceAvailability.objects.create(title='Device Repair', icon='ti-tool', order=1)
        ServiceAvailability.objects.create(title='Hidden', is_active=False, order=2)
        self.area = ServingArea.objects.create(city='Surat')

    def titles(self, resp):
        self.assertEqual(resp.status_code, 200)
        return [i['title'] for i in resp.json()]

    def test_lists_active_items_in_order_unpaginated(self):
        resp = self.client.get(self.url)
        self.assertEqual(self.titles(resp), ['Doorstep Delivery', 'Device Repair'])
        self.assertEqual(set(resp.json()[0]), {'id', 'icon', 'title', 'description'})

    def test_area_without_selection_gets_everything(self):
        self.assertEqual(self.titles(self.client.get(self.url, {'area': 'surat'})),
                         ['Doorstep Delivery', 'Device Repair'])

    def test_area_selection_narrows_the_list(self):
        self.area.availability.set([self.repair])
        self.assertEqual(self.titles(self.client.get(self.url, {'area': 'surat'})), ['Device Repair'])

    def test_unknown_area_is_404(self):
        self.assertEqual(self.client.get(self.url, {'area': 'nowhere'}).status_code, 404)

    def test_pages_point_the_strip_at_the_api(self):
        self.assertContains(self.client.get(reverse('pages:serving_areas')), f'data-api="{self.url}"')
        self.assertContains(self.client.get(self.area.get_absolute_url()), f'data-api="{self.url}?area=surat"')
