from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import BlogPost, BlogCategory
from .forms import BlogCommentForm


def _published():
    return BlogPost.objects.filter(status='published').select_related('category', 'author')


def blog_list(request):
    posts      = _published()
    categories = BlogCategory.objects.filter(is_active=True)
    query      = request.GET.get('q', '').strip()
    tag        = request.GET.get('tag', '').strip()

    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query)
        )
    if tag:
        posts = posts.filter(tags__name__in=[tag]).distinct()

    featured = posts.filter(is_featured=True).first()
    if not query and not tag:
        list_posts = posts.exclude(pk=featured.pk) if featured else posts
    else:
        list_posts = posts

    paginator = Paginator(list_posts, 9)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'blog/list.html', {
        'page_obj':        page_obj,
        'posts':           page_obj.object_list,
        'featured_post':   featured if not query and not tag else None,
        'categories':      categories,
        'popular_posts':   _published().order_by('-views_count')[:5],
        'query':           query,
        'active_tag':      tag,
        'page_title':      'Blog & News',
        'meta_description': 'Latest electronics news, buying guides, reviews and tech tips from TechZone.',
    })


def blog_category(request, slug):
    category   = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    posts      = _published().filter(category=category)
    paginator  = Paginator(posts, 9)
    page_obj   = paginator.get_page(request.GET.get('page'))

    return render(request, 'blog/list.html', {
        'page_obj':        page_obj,
        'posts':           page_obj.object_list,
        'categories':      BlogCategory.objects.filter(is_active=True),
        'popular_posts':   _published().order_by('-views_count')[:5],
        'active_category': category,
        'page_title':      category.meta_title or f'{category.name} — Blog',
        'meta_description': category.meta_description or category.description,
    })


def blog_detail(request, slug):
    post = get_object_or_404(_published(), slug=slug)

    # Count a view once per session
    viewed = request.session.get('viewed_posts', [])
    if post.pk not in viewed:
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        viewed.append(post.pk)
        request.session['viewed_posts'] = viewed

    # Related posts: same category, then recent
    related = (_published()
               .filter(category=post.category)
               .exclude(pk=post.pk)[:3]) if post.category else _published().exclude(pk=post.pk)[:3]

    crumbs = [{'title': 'Home', 'url': reverse('core:homepage')},
              {'title': 'Blog', 'url': reverse('blog:list')}]
    if post.category:
        crumbs.append({'title': post.category.name, 'url': post.category.get_absolute_url()})
    crumbs.append({'title': post.title, 'url': post.get_absolute_url()})

    return render(request, 'blog/detail.html', {
        'post':           post,
        'related_posts':  related,
        'comment_form':   BlogCommentForm(),
        'comments':       post.approved_comments,
        'categories':     BlogCategory.objects.filter(is_active=True),
        'popular_posts':  _published().order_by('-views_count').exclude(pk=post.pk)[:5],
        'breadcrumbs':    crumbs,
        'page_title':     post.meta_title or post.title,
        'meta_description': post.meta_description or post.excerpt,
    })


@require_POST
def post_comment(request, slug):
    post = get_object_or_404(_published(), slug=slug)
    if not post.allow_comments:
        messages.error(request, 'Comments are closed for this post.')
        return redirect(post.get_absolute_url())

    form = BlogCommentForm(request.POST)
    if form.is_valid():
        comment      = form.save(commit=False)
        comment.post = post
        comment.save()
        msg = 'Thank you! Your comment will appear after moderation.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        messages.success(request, msg)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors})
        messages.error(request, 'Please correct the errors in your comment.')
    return redirect(post.get_absolute_url() + '#comments')
