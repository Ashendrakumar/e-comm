"""Mobile-app API: catalog filters, detail extras, reviews, enquiries, compare, wishlist."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.models import Brand, SiteSettings
from .models import (Category, FAQ, Product, ProductAttribute, ProductAttributeValue, ProductInquiry,
                     ProductVariant, Review, Wishlist)


class CatalogFixture(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.tv     = Category.objects.create(name='TV')
        self.oled   = Category.objects.create(name='OLED', parent=self.tv)
        self.acme   = Brand.objects.create(name='Acme')
        self.zeta   = Brand.objects.create(name='Zeta')
        self.a = Product.objects.create(name='Acme OLED 55', category=self.oled, brand=self.acme,
                                        price=Decimal('1000'), sale_price=Decimal('700'), stock=5,
                                        color='Black', is_featured=True)
        self.b = Product.objects.create(name='Zeta LED 43', category=self.tv, brand=self.zeta,
                                        price=Decimal('400'), stock=0, color='Silver', is_new_arrival=False)
        Review.objects.create(product=self.a, name='R', email='r@x.com', rating=5, content='Great', is_approved=True)
        Review.objects.create(product=self.a, name='S', email='s@x.com', rating=3, content='Fine', is_approved=True)
        Review.objects.create(product=self.b, name='T', email='t@x.com', rating=1, content='Nope', is_approved=False)

    def slugs(self, url):
        return sorted(p['slug'] for p in self.client.get(url).json()['results'])

    def login(self, username='asha'):
        user = User.objects.create_user(username, f'{username}@example.com', 'Correct-Horse-42',
                                        first_name='Asha')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=user).key}')
        return user


class ProductListApiTests(CatalogFixture):
    def test_category_filter_includes_subcategories(self):
        self.assertEqual(self.slugs('/api/v1/products/?category=tv'), ['acme-oled-55', 'zeta-led-43'])
        self.assertEqual(self.slugs('/api/v1/products/?category=oled'), ['acme-oled-55'])
        self.assertEqual(self.slugs('/api/v1/products/?category=nope'), [])

    def test_filters(self):
        cases = {
            'brand=acme,zeta': 2, 'brand=zeta': 1, 'color=black': 1, 'in_stock=1': 1, 'on_sale=1': 1,
            'new_arrival=1': 1, 'min_rating=4': 1, 'min_discount=30': 1, 'min_discount=31': 0,
            'min_price=500': 1, 'max_price=abc': 2, f'ids={self.b.pk},junk': 1, 'search=zeta': 1,
        }
        for query, expected in cases.items():
            self.assertEqual(self.client.get(f'/api/v1/products/?{query}').json()['count'], expected, query)

    def test_card_fields_and_query_count(self):
        for i in range(10):
            Product.objects.create(name=f'Extra {i}', category=self.tv, price=Decimal('10'))
        with self.assertNumQueries(4):          # count, page, images prefetch, (no N+1 for ratings)
            resp = self.client.get('/api/v1/products/?ordering=-avg_rating')
        card = resp.json()['results'][0]
        self.assertEqual(card['slug'], 'acme-oled-55')
        self.assertEqual((card['average_rating'], card['review_count']), (4.0, 2))
        self.assertEqual((card['brand_slug'], card['category_slug']), ('acme', 'oled'))
        self.assertFalse(card['is_wishlisted'])

    def test_search_suggestions(self):
        body = self.client.get('/api/v1/products/search-suggestions/?q=acm').json()
        self.assertEqual([p['slug'] for p in body['products']], ['acme-oled-55'])
        self.assertEqual(body['brands'], [{'name': 'Acme', 'slug': 'acme'}])
        self.assertEqual(self.client.get('/api/v1/products/search-suggestions/?q=a').json()['products'], [])


class ProductDetailApiTests(CatalogFixture):
    def test_detail_extras(self):
        size = ProductAttribute.objects.create(name='Screen size')
        ProductAttributeValue.objects.create(product=self.a, attribute=size, value='55"')
        ProductVariant.objects.create(product=self.a, name='Wall mount', price_modifier=Decimal('50'))
        ProductVariant.objects.create(product=self.a, name='Old', is_active=False)
        FAQ.objects.create(product=self.a, question='Wall mount?', answer='Yes')

        body = self.client.get(f'/api/v1/products/{self.a.slug}/').json()
        self.assertEqual(body['specifications'], [{'name': 'Screen size', 'value': '55"'}])
        self.assertEqual([(v['name'], v['price']) for v in body['variants']], [('Wall mount', '750.00')])
        self.assertEqual(body['faqs'], [{'question': 'Wall mount?', 'answer': 'Yes'}])
        self.assertEqual([c['slug'] for c in body['breadcrumbs']], ['tv', 'oled'])
        self.assertEqual(body['rating_distribution'][0], {'stars': 5, 'count': 1, 'percent': 50})
        self.assertTrue(body['web_url'].endswith(self.a.get_absolute_url()))

    def test_view_counted_once_per_viewer(self):
        for _ in range(3):
            self.client.get(f'/api/v1/products/{self.a.slug}/')
        self.a.refresh_from_db()
        self.assertEqual(self.a.views_count, 1)

    def test_inactive_product_is_404(self):
        Product.objects.filter(pk=self.b.pk).update(is_active=False)
        self.assertEqual(self.client.get(f'/api/v1/products/{self.b.slug}/').status_code, 404)

    def test_related_sections(self):
        Product.objects.create(name='Acme OLED 65', category=self.oled, brand=self.acme, price=Decimal('1500'))
        body = self.client.get(f'/api/v1/products/{self.a.slug}/related/').json()
        self.assertEqual(set(body), {'related', 'frequently_viewed_together', 'popular_in_category', 'same_brand'})
        self.assertEqual([p['slug'] for p in body['related']], ['acme-oled-65'])
        self.assertEqual([p['slug'] for p in body['same_brand']], ['acme-oled-65'])

    def test_compare(self):
        body = self.client.get(f'/api/v1/products/compare/?ids={self.a.pk},{self.b.pk}').json()
        self.assertEqual([p['slug'] for p in body['products']], ['acme-oled-55', 'zeta-led-43'])
        self.assertEqual(body['best_price'], '400.00')
        brand = next(r for r in body['general_rows'] if r['label'] == 'Brand')
        self.assertEqual(brand, {'label': 'Brand', 'values': ['Acme', 'Zeta'], 'differs': True})
        self.assertFalse(any(r['label'] == 'Warranty' for r in body['general_rows']))   # nobody has one


class ReviewAndEnquiryApiTests(CatalogFixture):
    def test_reviews_list_only_approved_and_sorts(self):
        body = self.client.get(f'/api/v1/products/{self.a.slug}/reviews/?sort=rating_low').json()
        self.assertEqual([r['rating'] for r in body['results']], [3, 5])
        self.assertEqual(self.client.get(f'/api/v1/products/{self.b.slug}/reviews/').json()['count'], 0)

    def test_guest_review_needs_name_and_email(self):
        url  = f'/api/v1/products/{self.b.slug}/reviews/'
        resp = self.client.post(url, {'rating': 4, 'content': 'Solid telly overall.'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())

    def test_signed_in_review_is_prefilled_linked_and_pending(self):
        user = self.login()
        resp = self.client.post(f'/api/v1/products/{self.b.slug}/reviews/',
                                {'rating': 4, 'content': 'Solid telly overall.'}, format='json')
        self.assertEqual(resp.status_code, 201)
        review = Review.objects.get(user=user)
        self.assertEqual((review.name, review.email, review.is_approved), ('Asha', 'asha@example.com', False))
        mine = self.client.get('/api/v1/auth/me/reviews/').json()['results']
        self.assertEqual([(r['product']['slug'], r['is_approved']) for r in mine], [('zeta-led-43', False)])

    def test_helpful_vote_counted_once(self):
        review = Review.objects.filter(is_approved=True).first()
        first  = self.client.post(f'/api/v1/reviews/{review.pk}/helpful/').json()
        again  = self.client.post(f'/api/v1/reviews/{review.pk}/helpful/').json()
        self.assertEqual((first['helpful_count'], first['counted']), (1, True))
        self.assertEqual((again['helpful_count'], again['counted']), (1, False))

    def test_product_enquiry_saves_and_emails(self):
        s = SiteSettings.get_settings()
        s.notification_email = 'owner@example.com'
        s.save()
        resp = self.client.post(f'/api/v1/products/{self.a.slug}/inquiry/',
                                {'name': 'Priya', 'email': 'priya@example.com', 'phone': '9000000000',
                                 'message': 'Is the 55 inch in stock?'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ProductInquiry.objects.get().product, self.a)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])

    def test_product_enquiry_validation(self):
        resp = self.client.post(f'/api/v1/products/{self.a.slug}/inquiry/',
                                {'name': 'P', 'email': 'bad', 'phone': 'abc', 'message': 'hi'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(set(resp.json()), {'name', 'email', 'phone', 'message'})


class WishlistApiTests(CatalogFixture):
    def test_requires_sign_in(self):
        self.assertEqual(self.client.get('/api/v1/wishlist/').status_code, 401)

    def test_add_list_remove(self):
        self.login()
        self.assertEqual(self.client.post('/api/v1/wishlist/', {'product_id': str(self.a.pk)}).status_code, 201)
        self.assertEqual(self.client.post('/api/v1/wishlist/', {'product_id': str(self.a.pk)}).status_code, 200)
        self.assertEqual(self.client.post('/api/v1/wishlist/', {'product_id': 'junk'}).status_code, 400)

        items = self.client.get('/api/v1/wishlist/').json()['results']
        self.assertEqual([i['product']['slug'] for i in items], ['acme-oled-55'])
        self.assertTrue(items[0]['product']['is_wishlisted'])
        self.assertEqual(self.client.get('/api/v1/wishlist/ids/').json(), [str(self.a.pk)])

        self.assertEqual(self.client.delete(f'/api/v1/wishlist/{self.a.pk}/').status_code, 204)
        self.assertEqual(self.client.get('/api/v1/wishlist/ids/').json(), [])

    def test_sync_merges_guest_wishlist(self):
        user = self.login()
        Wishlist.objects.create(user=user, product=self.a)
        resp = self.client.post('/api/v1/wishlist/sync/',
                                {'product_ids': [str(self.a.pk), str(self.b.pk), 'junk']}, format='json')
        self.assertEqual(sorted(resp.json()), sorted([str(self.a.pk), str(self.b.pk)]))

    def test_users_only_see_their_own(self):
        other = User.objects.create_user('other', 'o@example.com', 'x')
        Wishlist.objects.create(user=other, product=self.a)
        self.login()
        self.assertEqual(self.client.get('/api/v1/wishlist/ids/').json(), [])


class CategoryApiTests(CatalogFixture):
    def test_tree_and_detail(self):
        tree = self.client.get('/api/v1/categories/tree/').json()
        self.assertEqual([(c['slug'], [k['slug'] for k in c['children']]) for c in tree], [('tv', ['oled'])])
        detail = self.client.get('/api/v1/categories/oled/').json()
        self.assertEqual([c['slug'] for c in detail['breadcrumbs']], ['tv', 'oled'])
        self.assertEqual((detail['parent_slug'], detail['product_count']), ('tv', 1))

    def test_root_and_parent_filters(self):
        self.assertEqual([c['slug'] for c in self.client.get('/api/v1/categories/?root=1').json()['results']],
                         ['tv'])
        self.assertEqual([c['slug'] for c in self.client.get('/api/v1/categories/?parent=tv').json()['results']],
                         ['oled'])
