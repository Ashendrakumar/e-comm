from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    # Services
    path('services/', views.services_list, name='services'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
    path('services/<slug:slug>/inquiry/', views.service_inquiry, name='service_inquiry'),

    # Serving areas
    path('areas/', views.serving_areas, name='serving_areas'),
    path('areas/<slug:slug>/', views.area_detail, name='area_detail'),

    # FAQs
    path('faqs/', views.faqs, name='faqs'),

    # CMS flat pages (keep last — catch-all slug)
    path('p/<slug:slug>/', views.flatpage, name='flatpage'),
]
