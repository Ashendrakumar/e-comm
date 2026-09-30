"""REST API for the mobile app and the site's own scripts (Module 14) — mounted at /api/v1/.

Full endpoint reference: docs/MOBILE_API.md. Browse it live at /api/v1/ (DEBUG).
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts import api as accounts
from blog.api import BlogCategoryViewSet, BlogPostViewSet
from core.api import BannerViewSet, ConfigView, ContactView, HomeView, NewsletterView, TestimonialViewSet
from pages.api import (FAQView, FlatPageViewSet, ServiceAvailabilityViewSet, ServiceViewSet,
                       ServingAreaViewSet)
from products.api import (BrandViewSet, CategoryViewSet, MyReviewsView, ProductViewSet,
                          ReviewHelpfulView, WishlistViewSet)

router = DefaultRouter()
# Catalog
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')
router.register('wishlist', WishlistViewSet, basename='wishlist')
# Content
router.register('banners', BannerViewSet, basename='banner')
router.register('testimonials', TestimonialViewSet, basename='testimonial')
router.register('services', ServiceViewSet, basename='service')
router.register('serving-areas', ServingAreaViewSet, basename='serving-area')
router.register('service-availability', ServiceAvailabilityViewSet, basename='service-availability')
router.register('pages', FlatPageViewSet, basename='page')
router.register('blog/categories', BlogCategoryViewSet, basename='blog-category')
router.register('blog/posts', BlogPostViewSet, basename='blog-post')

urlpatterns = [
    # Accounts (token auth)
    path('auth/register/', accounts.RegisterView.as_view(), name='api-register'),
    path('auth/login/', accounts.LoginView.as_view(), name='api-login'),
    path('auth/logout/', accounts.LogoutView.as_view(), name='api-logout'),
    path('auth/me/', accounts.MeView.as_view(), name='api-me'),
    path('auth/me/reviews/', MyReviewsView.as_view(), name='api-my-reviews'),
    path('auth/change-password/', accounts.ChangePasswordView.as_view(), name='api-change-password'),
    path('auth/password-reset/', accounts.PasswordResetView.as_view(), name='api-password-reset'),
    path('auth/password-reset/confirm/', accounts.PasswordResetConfirmView.as_view(),
         name='api-password-reset-confirm'),
    path('auth/delete-account/', accounts.DeleteAccountView.as_view(), name='api-delete-account'),

    # Site
    path('home/', HomeView.as_view(), name='api-home'),
    path('config/', ConfigView.as_view(), name='api-config'),
    path('faqs/', FAQView.as_view(), name='api-faqs'),
    path('contact/', ContactView.as_view(), name='api-contact'),
    path('newsletter/', NewsletterView.as_view(), name='api-newsletter'),
    path('reviews/<int:pk>/helpful/', ReviewHelpfulView.as_view(), name='api-review-helpful'),
] + router.urls
