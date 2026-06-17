"""Public REST API router (Module 14) — mounted at /api/v1/."""
from rest_framework.routers import DefaultRouter
from products.api import ProductViewSet, CategoryViewSet, BrandViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')

urlpatterns = router.urls
