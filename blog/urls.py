from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog_list, name='list'),
    path('category/<slug:slug>/', views.blog_category, name='category'),
    path('<slug:slug>/', views.blog_detail, name='detail'),
    path('<slug:slug>/comment/', views.post_comment, name='comment'),
]
