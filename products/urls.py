from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('',                                      views.product_list,        name='list'),
    path('categories/',                           views.categories_overview, name='categories'),
    path('compare/',                              views.compare_products,    name='compare'),
    path('category/<slug:slug>/',                 views.category_detail,     name='category'),
    path('ajax/filter/',                          views.ajax_filter,         name='ajax_filter'),
    path('ajax/quick-view/<slug:slug>/',          views.quick_view,          name='quick_view'),
    path('ajax/wishlist/toggle/<uuid:pk>/',       views.toggle_wishlist,     name='toggle_wishlist'),
    path('ajax/review/<slug:slug>/',              views.submit_review,       name='submit_review'),
    path('ajax/inquiry/<slug:slug>/',             views.submit_inquiry,      name='submit_inquiry'),
    path('ajax/helpful/<int:review_id>/',         views.mark_helpful,        name='mark_helpful'),
    path('ajax/related/<slug:slug>/',             views.ajax_related,        name='ajax_related'),
    path('<slug:slug>/',                          views.product_detail,      name='detail'),
]
