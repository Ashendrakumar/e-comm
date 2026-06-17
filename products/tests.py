from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from core.models import Brand
from .models import Category, Product, Review


class ProductModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Laptops')
        self.brand = Brand.objects.create(name='Acme')
        self.p = Product.objects.create(
            name='Acme UltraBook 14', category=self.cat, brand=self.brand,
            price=Decimal('1000.00'), sale_price=Decimal('800.00'), stock=3,
        )

    def test_slug_and_sku_autoset(self):
        self.assertEqual(self.p.slug, 'acme-ultrabook-14')
        self.assertTrue(self.p.sku.startswith('TZ-'))

    def test_pricing_properties(self):
        self.assertEqual(self.p.effective_price, Decimal('800.00'))
        self.assertEqual(self.p.discount_percent, 20)
        self.assertEqual(self.p.savings_amount, Decimal('200.00'))

    def test_stock_flags(self):
        self.assertTrue(self.p.is_in_stock)
        self.assertTrue(self.p.is_low_stock)  # 3 <= default threshold 5
        self.p.stock = 0
        self.assertFalse(self.p.is_in_stock)

    def test_average_rating_only_counts_approved(self):
        Review.objects.create(product=self.p, name='A', email='a@x.com', rating=4, content='ok', is_approved=True)
        Review.objects.create(product=self.p, name='B', email='b@x.com', rating=2, content='meh', is_approved=False)
        self.assertEqual(self.p.average_rating, 4)
        self.assertEqual(self.p.review_count, 1)


class ProductViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Phones')
        self.p = Product.objects.create(name='Phone X', category=self.cat, price=Decimal('500'), stock=10)

    def test_list_page(self):
        resp = self.client.get(reverse('products:list'))
        self.assertEqual(resp.status_code, 200)

    def test_category_page(self):
        resp = self.client.get(self.cat.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    def test_detail_page_and_jsonld(self):
        resp = self.client.get(self.p.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '"@type": "Product"')

    def test_inactive_product_hidden(self):
        self.p.is_active = False
        self.p.save()
        resp = self.client.get(reverse('products:list'))
        self.assertNotContains(resp, 'Phone X')


class ProductAPITests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Cameras')
        self.brand = Brand.objects.create(name='Zoomz')
        self.p = Product.objects.create(
            name='Zoomz DSLR', category=self.cat, brand=self.brand,
            price=Decimal('1200'), stock=4, is_featured=True,
        )
        Product.objects.create(name='Cheapie Cam', category=self.cat, price=Decimal('100'), stock=0)

    def test_product_list_endpoint(self):
        resp = self.client.get('/api/v1/products/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 2)

    def test_featured_filter(self):
        resp = self.client.get('/api/v1/products/?featured=1')
        self.assertEqual(resp.json()['count'], 1)

    def test_price_filter(self):
        resp = self.client.get('/api/v1/products/?max_price=200')
        self.assertEqual(resp.json()['count'], 1)

    def test_detail_endpoint(self):
        resp = self.client.get(f'/api/v1/products/{self.p.slug}/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['slug'], self.p.slug)
        self.assertIn('images', data)
        self.assertIn('reviews', data)

    def test_categories_endpoint(self):
        resp = self.client.get('/api/v1/categories/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 1)
