from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
from .models import Service, ServingArea, HomepageBanner, HomepageSection


def services_list(request):
    services = Service.objects.filter(is_active=True).order_by('order')
    return render(request, 'pages/services.html', {
        'services':   services,
        'page_title': 'Our Services',
    })


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    return render(request, 'pages/service_detail.html', {
        'service':    service,
        'page_title': service.title,
    })


def serving_areas(request):
    areas = ServingArea.objects.filter(is_active=True).order_by('city')
    default_cities = [
        'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar',
        'Anand', 'Nadiad', 'Bharuch', 'Navsari', 'Vapi',
        'Morbi', 'Junagadh', 'Bhavnagar', 'Mehsana', 'Sānand',
    ]
    return render(request, 'pages/serving_areas.html', {
        'areas':         areas,
        'default_cities': default_cities,
        'page_title':    'Serving Areas',
    })


def area_detail(request, slug):
    area = get_object_or_404(ServingArea, slug=slug, is_active=True)
    return render(request, 'pages/area_detail.html', {
        'area':       area,
        'page_title': area.city,
    })


def api_homepage_sections(request):
    sections = HomepageSection.objects.filter(is_active=True)
    banners = HomepageBanner.objects.filter(is_active=True)

    sections_data = [
        {
            'id': s.id,
            'name': s.name,
            'section_type': s.section_type,
            'title': s.title,
            'subtitle': s.subtitle,
            'content': s.content,
            'template': s.template,
            'order': s.order,
        }
        for s in sections
    ]

    banners_data = [
        {
            'id': b.id,
            'title': b.title,
            'subtitle': b.subtitle,
            'image': b.image.url if b.image else '',
            'image_mobile': b.image_mobile.url if b.image_mobile else '',
            'link': b.link,
            'link_text': b.link_text,
            'badge_text': b.badge_text,
            'badge_color': b.badge_color,
            'order': b.order,
        }
        for b in banners
    ]

    return JsonResponse({
        'sections': sections_data,
        'banners': banners_data,
    })


@require_http_methods(['POST'])
def api_sections_reorder(request):
    try:
        data = json.loads(request.body)
        section_ids = data.get('section_ids', [])

        with transaction.atomic():
            for order, section_id in enumerate(section_ids):
                HomepageSection.objects.filter(id=section_id).update(order=order)

        return JsonResponse({'success': True, 'message': 'Sections reordered'})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(['POST'])
def api_banners_reorder(request):
    try:
        data = json.loads(request.body)
        banner_ids = data.get('banner_ids', [])

        with transaction.atomic():
            for order, banner_id in enumerate(banner_ids):
                HomepageBanner.objects.filter(id=banner_id).update(order=order)

        return JsonResponse({'success': True, 'message': 'Banners reordered'})
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
