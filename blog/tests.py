from django.test import TestCase
from django.urls import reverse
from .models import BlogCategory, BlogPost


class BlogTests(TestCase):
    def setUp(self):
        self.cat = BlogCategory.objects.create(name='Buying Guides')
        self.post = BlogPost.objects.create(
            title='How to choose a laptop',
            category=self.cat,
            content='word ' * 400,
            status='published',
        )

    def test_slug_and_reading_time_autoset(self):
        self.assertEqual(self.post.slug, 'how-to-choose-a-laptop')
        self.assertEqual(self.post.reading_minutes, 2)
        self.assertTrue(self.post.published_at)

    def test_list_page(self):
        resp = self.client.get(reverse('blog:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'How to choose a laptop')

    def test_detail_increments_views(self):
        resp = self.client.get(self.post.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, 1)

    def test_draft_hidden(self):
        BlogPost.objects.create(title='Secret draft', content='x', status='draft')
        resp = self.client.get(reverse('blog:list'))
        self.assertNotContains(resp, 'Secret draft')
