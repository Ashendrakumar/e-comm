from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('',                                       views.product_list,            name='list'),
    path('categories/',                           views.categories_overview,     name='categories'),
    path('compare/',                              views.compare_products,        name='compare'),
    path('category/<slug:slug>/',                 views.category_detail,         name='category'),
    path('ajax/filter/',                          views.ajax_filter,             name='ajax_filter'),
    path('ajax/quick-view/<slug:slug>/',          views.quick_view,              name='quick_view'),
    path('ajax/wishlist/toggle/<uuid:pk>/',       views.toggle_wishlist,         name='toggle_wishlist'),
    path('ajax/rating-dist/<slug:slug>/',         views.rating_distribution,     name='rating_dist'),
    path('<slug:slug>/inquiry/',                  views.submit_inquiry,          name='submit_inquiry'),
    path('<slug:slug>/review/',                   views.submit_review,           name='submit_review'),
    path('<slug:slug>/stock-alert/',              views.stock_alert_signup,      name='stock_alert'),
    path('<slug:slug>/',                          views.product_detail,          name='detail'),
]

