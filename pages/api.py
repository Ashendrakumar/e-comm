"""DRF endpoints for the pages app (mounted under /api/v1/ by techzone/api_urls.py).

    GET /api/v1/service-availability/              every active item
    GET /api/v1/service-availability/?area=<slug>  items offered in that city
                                                   (404 for an unknown/inactive city)
"""
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets

from .models import ServiceAvailability, ServingArea


class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServiceAvailability
        fields = ['id', 'icon', 'title', 'description']


class ServiceAvailabilityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceAvailabilitySerializer
    pagination_class = None          # a short, fixed list — return it as a plain array

    def get_queryset(self):
        slug = self.request.query_params.get('area')
        if slug:
            area = get_object_or_404(ServingArea, slug=slug, is_active=True)
            return area.available_services()
        return ServiceAvailability.objects.filter(is_active=True)
