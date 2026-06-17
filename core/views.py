from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import Banner, Testimonial, WhyChooseUs, Brand
from .forms import ContactForm, NewsletterForm
from products.models import Category, Product


def homepage(request):
    from pages.models import Service, ServingArea
    from django.core.cache import cache

    # Product lists change often (stock/featured flags) — query live.
    featured_products = Product.objects.filter(is_featured=True, is_active=True).select_related('category', 'brand').prefetch_related('images')[:8]
    trending_products = Product.objects.filter(is_trending=True, is_active=True).select_related('category', 'brand').prefetch_related('images')[:8]
    new_arrivals      = Product.objects.filter(is_new_arrival=True, is_active=True).order_by('-created_at').select_related('category', 'brand').prefetch_related('images')[:8]

    # Rarely-changing display lists — cache for 10 minutes to cut DB hits.
    hero_banners        = cache.get_or_set('home_hero_banners',  lambda: list(Banner.objects.filter(banner_type='hero', is_active=True)[:3]), 600)
    promo_banners       = cache.get_or_set('home_promo_banners', lambda: list(Banner.objects.filter(banner_type='promo', is_active=True)[:4]), 600)
    featured_categories = cache.get_or_set('home_featured_cats', lambda: list(Category.objects.filter(is_featured=True, is_active=True, parent=None)[:10]), 600)
    featured_brands     = cache.get_or_set('home_featured_brands', lambda: list(Brand.objects.filter(is_featured=True, is_active=True)[:12]), 600)
    testimonials        = cache.get_or_set('home_testimonials',  lambda: list(Testimonial.objects.filter(is_active=True)[:6]), 600)
    why_choose_us       = cache.get_or_set('home_why_choose_us', lambda: list(WhyChooseUs.objects.filter(is_active=True)[:6]), 600)

    # Services for homepage — from DB or hardcoded fallback
    homepage_services = list(Service.objects.filter(is_active=True).order_by('order')[:6])
    if not homepage_services:
        # Fallback dataclass-style dicts so template works identically
        homepage_services = [
            {'icon': 'ti-bulb',             'title': 'Product Consultation'},
            {'icon': 'ti-tool',             'title': 'Installation Services'},
            {'icon': 'ti-device-mobile',    'title': 'Device Repair'},
            {'icon': 'ti-shield-checkered', 'title': 'Warranty Support'},
            {'icon': 'ti-package',          'title': 'Bulk Orders'},
            {'icon': 'ti-home',             'title': 'Home Delivery'},
        ]

    context = {
        'hero_banners':       hero_banners,
        'promo_banners':      promo_banners,
        'featured_products':  featured_products,
        'trending_products':  trending_products,
        'new_arrivals':       new_arrivals,
        'featured_categories': featured_categories,
        'featured_brands':    featured_brands,
        'testimonials':       testimonials,
        'why_choose_us':      why_choose_us,
        'homepage_services':  homepage_services,
        'serving_areas':      ServingArea.objects.filter(is_active=True).order_by('-is_featured', 'city')[:10],
        'serving_area_cities': ['Ahmedabad','Surat','Vadodara','Rajkot','Gandhinagar','Anand','Nadiad','Bharuch','Navsari','Vapi'],
        'contact_form':       ContactForm(),
        'newsletter_form':    NewsletterForm(),
        'page_title':         'TechZone — Premium Electronics Store',
        'meta_description':   'Shop the latest electronics including mobiles, laptops, TVs, cameras and more at TechZone.',
    }
    return render(request, 'core/homepage.html', context)


def _notify_inquiry(inquiry):
    """Best-effort email notification to the business (console backend in dev)."""
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        send_mail(
            subject=f'[{inquiry.get_inquiry_type_display()}] {inquiry.subject}',
            message=(f'From: {inquiry.name} <{inquiry.email}> {inquiry.phone}\n\n{inquiry.message}'),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass


@require_POST
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        inquiry = form.save()
        _notify_inquiry(inquiry)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Thank you! We will get back to you shortly.'})
        messages.success(request, 'Thank you for reaching out! We will contact you within 24 hours.')
        return redirect(request.META.get('HTTP_REFERER', 'core:homepage'))
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors})
    messages.error(request, 'Please correct the errors below.')
    return redirect(request.META.get('HTTP_REFERER', 'core:homepage'))


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        subscription, created = __import__('core.models', fromlist=['NewsletterSubscription']).NewsletterSubscription.objects.get_or_create(
            email=form.cleaned_data['email'],
            defaults={'is_active': True}
        )
        if created:
            msg = 'Successfully subscribed to our newsletter!'
        else:
            subscription.is_active = True
            subscription.save()
            msg = 'You are already subscribed!'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        messages.success(request, msg)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please enter a valid email.'})
        messages.error(request, 'Please enter a valid email address.')
    return redirect('core:homepage')


def contact_page(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            _notify_inquiry(inquiry)
            messages.success(request, 'Message sent successfully! Our team will get back to you within 24 hours.')
            form = ContactForm()
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    return render(request, 'pages/contact.html', {
        'form':             form,
        'page_title':       'Contact Us',
        'meta_description': 'Get in touch with TechZone — call, WhatsApp, email or visit our store. We respond within 24 hours.',
    })


def about_page(request):
    why_choose_us = WhyChooseUs.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    return render(request, 'pages/about.html', {
        'why_choose_us': why_choose_us,
        'testimonials': testimonials,
        'page_title': 'About TechZone',
    })


def robots_txt(request):
    host  = request.get_host()
    lines = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /products/ajax/',
        'Disallow: /pages/services/*/inquiry/',
        'Allow: /',
        '',
        f'Sitemap: {request.scheme}://{host}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
