from django.shortcuts import render, get_object_or_404
from .models import Service, ServingArea


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
