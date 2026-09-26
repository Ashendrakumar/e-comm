import os
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


from django.core import mail
from core.models import SiteSettings


class WishlistAndEnquiryTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Phones')
        self.a = Product.objects.create(name='Phone A', category=self.cat, price=Decimal('100'), stock=2)
        self.b = Product.objects.create(name='Phone B', category=self.cat, price=Decimal('200'), stock=2)

    def test_wishlist_page_lists_saved_ids_in_order_and_ignores_junk(self):
        url = reverse('products:wishlist')
        resp = self.client.get(url, {'ids': [str(self.b.pk), 'not-a-uuid', str(self.a.pk), str(self.b.pk)]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([p.pk for p in resp.context['products']], [self.b.pk, self.a.pk])

    def test_empty_wishlist_page_renders(self):
        resp = self.client.get(reverse('products:wishlist'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Your wishlist is empty')

    def test_product_enquiry_emails_the_notification_address(self):
        s = SiteSettings.get_settings()
        s.notification_email = 'owner@example.com'
        s.save()
        resp = self.client.post(reverse('products:submit_inquiry', args=[self.a.slug]),
                                {'name': 'Priya', 'email': 'priya@example.com', 'phone': '9000000000',
                                 'message': 'Is it in stock?'},
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(resp.json()['success'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])
        self.assertIn('Phone A', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].reply_to, ['priya@example.com'])


import tempfile
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from .models import ProductImage


class ImportProductImagesTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.src = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        cat = Category.objects.create(name='Phones')
        self.cam = Product.objects.create(name='Canon EOS R50', category=cat, price=Decimal('1'))
        self.phone = Product.objects.create(name='iPhone 15', category=cat, price=Decimal('1'))

    def tearDown(self):
        self.override.disable()
        self.media.cleanup(); self.src.cleanup()

    def _img(self, path, size=(2400, 1600)):
        from PIL import Image
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', size, (15, 118, 110)).save(path)

    def test_folder_per_product_and_loose_files(self):
        root = Path(self.src.name)
        d = root / 'Cameras' / self.cam.sku
        for n in ('10', '2', 'main'):
            self._img(d / f'{n}.jpg')
        self._img(root / 'iphone-15.jpg', (800, 800))          # whole name = slug, "15" is not an index
        call_command('import_product_images', str(root), apply=True, stdout=open(os.devnull, 'w'))

        imgs = list(self.cam.images.order_by('order'))
        self.assertEqual(len(imgs), 3)
        self.assertTrue(imgs[0].is_primary)
        self.assertTrue(imgs[0].image.name.endswith('-1.webp'))
        from PIL import Image
        with Image.open(imgs[0].image.path) as im:
            self.assertLessEqual(max(im.size), 1600)
        self.assertEqual(self.phone.images.count(), 1)

    def test_skip_mode_leaves_products_with_images_alone(self):
        root = Path(self.src.name)
        self._img(root / self.cam.sku / 'a.jpg')
        call_command('import_product_images', str(root), apply=True, stdout=open(os.devnull, 'w'))
        call_command('import_product_images', str(root), apply=True, stdout=open(os.devnull, 'w'))
        self.assertEqual(self.cam.images.count(), 1)

    def test_dry_run_saves_nothing(self):
        root = Path(self.src.name)
        self._img(root / self.cam.sku / 'a.jpg')
        call_command('import_product_images', str(root), stdout=open(os.devnull, 'w'))
        self.assertEqual(self.cam.images.count(), 0)

    def test_sku_dash_name_folders_and_name_fallback(self):
        root = Path(self.src.name)
        self._img(root / 'Cameras' / f'{self.cam.sku} - Canon EOS R50' / 'main.jpg')
        self._img(root / 'Phones' / 'TZ-OLDSKU99 - iPhone 15' / 'main.jpg')   # stale SKU, name still matches
        call_command('import_product_images', str(root), apply=True, stdout=open(os.devnull, 'w'))
        self.assertEqual(self.cam.images.count(), 1)
        self.assertEqual(self.phone.images.count(), 1)

    def test_create_folders_makes_one_folder_per_product(self):
        from products.image_import import create_folders
        root = Path(self.src.name) / 'Drive'
        ProductImage.objects.create(product=self.phone, image='products/x.jpg')   # has photos: still gets one
        created, existing = create_folders(root)
        self.assertEqual((len(created), existing), (2, 0))
        self.assertTrue((root / 'Phones' / f'{self.cam.sku} - Canon EOS R50').is_dir())
        created, existing = create_folders(root)                 # safe to run again
        self.assertEqual((len(created), existing), (0, 2))
        self.assertEqual(len(create_folders(root / 'new', only_missing=True)[0]), 1)

    def test_create_folders_keeps_renamed_or_moved_folders(self):
        from products.image_import import create_folders
        root = Path(self.src.name)
        (root / 'Old category' / self.cam.sku).mkdir(parents=True)   # moved + renamed by hand
        created, existing = create_folders(root)
        self.assertEqual((len(created), existing), (1, 1))
        self.assertFalse((root / 'Phones' / f'{self.cam.sku} - Canon EOS R50').exists())

    def test_create_product_folders_command_and_missing_drive(self):
        root = Path(self.src.name) / 'Drive'
        call_command('create_product_folders', str(root), dry_run=True, stdout=open(os.devnull, 'w'))
        self.assertFalse(root.exists())
        call_command('create_product_folders', str(root), stdout=open(os.devnull, 'w'))
        self.assertEqual(len(list(root.glob('*/*'))), 2)
        with self.assertRaisesMessage(CommandError, 'Google Drive for desktop'):
            call_command('create_product_folders', str(root.parent / 'nope' / 'Drive'))

    def test_admin_preview_then_import(self):
        from django.contrib.auth.models import User
        admin = User.objects.create_superuser('boss', 'b@example.com', 'pw')
        self.client.force_login(admin)
        root = Path(self.src.name)
        self._img(root / self.cam.sku / 'main.jpg')
        url = reverse('admin:products_product_import_images')
        self.assertContains(self.client.get(reverse('admin:products_product_changelist')), 'Import images from Drive')
        resp = self.client.post(url, {'folder': str(root), 'mode': 'skip', 'action': 'preview'})
        self.assertContains(resp, 'nothing saved yet')
        self.assertEqual(self.cam.images.count(), 0)
        resp = self.client.post(url, {'folder': str(root), 'mode': 'skip', 'action': 'apply'})
        self.assertContains(resp, 'Import finished')
        self.assertEqual(self.cam.images.count(), 1)

