"""Mobile-app API: blog posts, categories, comments."""
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .models import BlogCategory, BlogComment, BlogPost


class BlogApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.guides = BlogCategory.objects.create(name='Guides')
        self.post = BlogPost.objects.create(title='Choosing a TV', category=self.guides, status='published',
                                            content='<p>Pick OLED.</p>')
        self.post.tags.add('tv')
        BlogPost.objects.create(title='Draft', content='wip')

    def test_list_filters_and_category_counts(self):
        self.assertEqual(self.client.get('/api/v1/blog/posts/').json()['count'], 1)
        self.assertEqual(self.client.get('/api/v1/blog/posts/?tag=tv').json()['count'], 1)
        self.assertEqual(self.client.get('/api/v1/blog/posts/?category=nope').json()['count'], 0)
        self.assertEqual(self.client.get('/api/v1/blog/categories/').json()[0]['post_count'], 1)

    def test_detail_counts_view_once_and_hides_drafts(self):
        for _ in range(2):
            body = self.client.get('/api/v1/blog/posts/choosing-a-tv/').json()
        self.assertEqual((body['content'], body['tags']), ('<p>Pick OLED.</p>', ['tv']))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, 1)
        self.assertEqual(self.client.get('/api/v1/blog/posts/draft/').status_code, 404)

    def test_comments(self):
        url  = '/api/v1/blog/posts/choosing-a-tv/comments/'
        resp = self.client.post(url, {'name': 'Kiran', 'email': 'k@example.com',
                                      'content': 'Very helpful, thanks!'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.client.get(url).json()['count'], 0)            # held for moderation
        BlogComment.objects.update(is_approved=True)
        self.assertEqual(self.client.get(url).json()['results'][0]['name'], 'Kiran')

        BlogPost.objects.filter(pk=self.post.pk).update(allow_comments=False)
        self.assertEqual(self.client.post(url, {'name': 'X'}, format='json').status_code, 403)
