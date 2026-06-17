from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from .models import Service, ServingArea, FlatPage, FAQCategory, GeneralFAQ
from .forms import ServiceInquiryForm


# ── Services ────────────────────────────────────────────────────────

def services_list(request):
    services = Service.objects.filter(is_active=True).prefetch_related('features').order_by('order')
    return render(request, 'pages/services.html', {
        'services':         services,
        'page_title':       'Our Services',
        'meta_description': 'Professional electronics services — consultation, installation, repair, warranty support, bulk orders and more.',
    })


def service_detail(request, slug):
    service       = get_object_or_404(Service, slug=slug, is_active=True)
    other_services = (Service.objects.filter(is_active=True)
                      .exclude(pk=service.pk).order_by('order')[:4])
    return render(request, 'pages/service_detail.html', {
        'service':          service,
        'other_services':   other_services,
        'inquiry_form':     ServiceInquiryForm(),
        'page_title':       service.meta_title or service.title,
        'meta_description': service.meta_description or service.short_description,
    })


@require_POST
def service_inquiry(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    form    = ServiceInquiryForm(request.POST)
    if form.is_valid():
        inquiry         = form.save(commit=False)
        inquiry.service = service
        inquiry.save()
        # Best-effort email notification (console backend in dev)
        try:
            send_mail(
                subject=f'New service inquiry: {service.title}',
                message=f'{inquiry.name} ({inquiry.email}, {inquiry.phone}) from {inquiry.city}:\n\n{inquiry.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        msg = 'Thank you! Our team will contact you shortly about this service.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        messages.success(request, msg)
        return redirect(service.get_absolute_url())
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors})
    messages.error(request, 'Please correct the errors and try again.')
    return redirect(service.get_absolute_url())


# ── Serving Areas ───────────────────────────────────────────────────

def serving_areas(request):
    areas          = ServingArea.objects.filter(is_active=True).order_by('city')
    featured_areas = areas.filter(is_featured=True)
    default_cities = [
        'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar',
        'Anand', 'Nadiad', 'Bharuch', 'Navsari', 'Vapi',
        'Morbi', 'Junagadh', 'Bhavnagar', 'Mehsana', 'Sānand',
    ]
    return render(request, 'pages/serving_areas.html', {
        'areas':          areas,
        'featured_areas': featured_areas,
        'default_cities': default_cities,
        'page_title':     'Serving Areas',
    })


def area_detail(request, slug):
    area  = get_object_or_404(ServingArea, slug=slug, is_active=True)
    other = ServingArea.objects.filter(is_active=True).exclude(pk=area.pk).order_by('city')[:12]
    return render(request, 'pages/area_detail.html', {
        'area':             area,
        'other_areas':      other,
        'page_title':       area.meta_title or f'Electronics Delivery & Service in {area.city}',
        'meta_description': area.meta_description or f'TechZone serves {area.city}, {area.state} with electronics delivery, installation and repair.',
    })


# ── CMS flat pages ──────────────────────────────────────────────────

def flatpage(request, slug):
    page = get_object_or_404(FlatPage, slug=slug, is_active=True)
    return render(request, 'pages/flatpage.html', {
        'page':             page,
        'page_title':       page.meta_title or page.title,
        'meta_description': page.meta_description,
    })


# ── FAQs ────────────────────────────────────────────────────────────

def faqs(request):
    categories = (FAQCategory.objects.filter(is_active=True)
                  .prefetch_related('faqs').order_by('order'))
    uncategorised = GeneralFAQ.objects.filter(is_active=True, category__isnull=True).order_by('order')
    return render(request, 'pages/faqs.html', {
        'categories':       categories,
        'uncategorised':    uncategorised,
        'page_title':       'Frequently Asked Questions',
        'meta_description': 'Answers to common questions about TechZone products, delivery, warranty and services.',
    })
