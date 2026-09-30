"""Blog endpoints under /api/v1/blog/ (mobile app).

    GET  /blog/categories/
    GET  /blog/posts/                   ?category=<slug> &tag=<name> &featured=1 &search= &ordering=
    GET  /blog/posts/{slug}/            full article (HTML) + related posts
    GET  /blog/posts/{slug}/comments/   approved comments
    POST /blog/posts/{slug}/comments/   {name, email, content} — held for moderation
"""
from django.db.models import Count, F, Q
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api_utils import first_time, flag, form_data, form_errors, rate_limited, user_defaults
from .forms import BlogCommentForm
from .models import BlogCategory, BlogComment, BlogPost


class BlogCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(source='num_posts', read_only=True)

    class Meta:
        model  = BlogCategory
        fields = ['id', 'name', 'slug', 'description', 'color', 'icon', 'post_count']


class BlogPostSerializer(serializers.ModelSerializer):
    category      = serializers.StringRelatedField()
    category_slug = serializers.SlugRelatedField(source='category', slug_field='slug', read_only=True)
    author        = serializers.CharField(source='display_author', read_only=True)

    class Meta:
        model  = BlogPost
        fields = ['id', 'title', 'slug', 'category', 'category_slug', 'author', 'featured_image',
                  'excerpt', 'is_featured', 'reading_minutes', 'views_count', 'published_at']


class BlogPostDetailSerializer(BlogPostSerializer):
    tags          = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()
    web_url       = serializers.SerializerMethodField()

    class Meta(BlogPostSerializer.Meta):
        fields = BlogPostSerializer.Meta.fields + ['content', 'tags', 'allow_comments', 'comment_count',
                                                  'related_posts', 'updated_at', 'web_url']

    def get_tags(self, obj):
        return list(obj.tags.names())

    def get_comment_count(self, obj):
        return obj.approved_comments.count()

    def get_related_posts(self, obj):
        qs = published().exclude(pk=obj.pk)
        if obj.category_id:
            qs = qs.filter(category_id=obj.category_id)
        return BlogPostSerializer(qs[:3], many=True, context=self.context).data

    def get_web_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) if request else obj.get_absolute_url()


class BlogCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BlogComment
        fields = ['id', 'name', 'content', 'created_at']


def published():
    return BlogPost.objects.filter(status='published').select_related('category', 'author')


class BlogCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BlogCategorySerializer
    lookup_field     = 'slug'
    pagination_class = None

    def get_queryset(self):
        return (BlogCategory.objects.filter(is_active=True)
                .annotate(num_posts=Count('posts', filter=Q(posts__status='published')))
                .order_by('order', 'name'))


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field    = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'views_count']
    ordering        = ['-published_at']

    def get_serializer_class(self):
        return BlogPostDetailSerializer if self.action == 'retrieve' else BlogPostSerializer

    def get_queryset(self):
        qs = published()
        p  = self.request.query_params
        if self.action == 'list':
            if p.get('category'):
                qs = qs.filter(category__slug=p['category'])
            if p.get('tag'):
                qs = qs.filter(tags__name__in=[p['tag']]).distinct()
            if flag(p, 'featured'):
                qs = qs.filter(is_featured=True)
        return qs

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        if first_time(request, f'post-view:{post.pk}'):         # once per viewer per day, like the site
            BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        return Response(self.get_serializer(post).data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, slug=None):
        post = self.get_object()
        if request.method == 'GET':
            page = self.paginate_queryset(post.approved_comments)
            return self.get_paginated_response(BlogCommentSerializer(page, many=True).data)

        if not post.allow_comments:
            return Response({'detail': 'Comments are closed for this post.'}, status=status.HTTP_403_FORBIDDEN)
        limited = rate_limited(request, 'blog-comment')
        if limited:
            return limited
        form = BlogCommentForm(form_data(request, BlogCommentForm.Meta.fields, **user_defaults(request)))
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        return Response({'detail': 'Thank you! Your comment will appear after moderation.'},
                        status=status.HTTP_201_CREATED)
