"""Public REST API router (Module 14) — mounted at /api/v1/."""
from rest_framework.routers import DefaultRouter
from products.api import ProductViewSet, CategoryViewSet, BrandViewSet
from pages.api import ServiceAvailabilityViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')
router.register('service-availability', ServiceAvailabilityViewSet, basename='service-availability')

urlpatterns = router.urls
