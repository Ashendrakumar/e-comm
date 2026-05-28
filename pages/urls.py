from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('services/', views.services_list, name='services'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
    path('areas/', views.serving_areas, name='serving_areas'),
    path('areas/<slug:slug>/', views.area_detail, name='area_detail'),
]
