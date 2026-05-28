from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('contact/', views.contact_page, name='contact'),
    path('about/', views.about_page, name='about'),
    path('ajax/contact/', views.contact_submit, name='contact_submit'),
    path('ajax/newsletter/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
