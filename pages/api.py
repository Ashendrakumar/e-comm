"""DRF endpoints for the pages app (mounted under /api/v1/ by techzone/api_urls.py).

    GET  /service-availability/              every active item
    GET  /service-availability/?area=<slug>  items offered in that city
                                             (404 for an unknown/inactive city)
    GET  /services/  /services/{slug}/       ?featured=1
    POST /services/{slug}/inquiry/           {name, email, phone?, city?, message}
    GET  /serving-areas/  /serving-areas/{slug}/
    GET  /serving-areas/check/?pincode=380015   is this pincode served, and by which city
    GET  /faqs/                              grouped by category
    GET  /pages/  /pages/{slug}/             CMS pages (About, Privacy, Terms ...)
"""
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_utils import flag, form_data, form_errors, rate_limited, user_defaults
from .forms import ServiceInquiryForm
from .models import FAQCategory, FlatPage, GeneralFAQ, Service, ServiceAvailability, ServingArea
from .views import notify_service_inquiry


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


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Service
        fields = ['id', 'title', 'slug', 'icon', 'short_description', 'image', 'color',
                  'price_info', 'is_featured']


class ServiceDetailSerializer(ServiceSerializer):
    features = serializers.SerializerMethodField()

    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + ['description', 'banner', 'cta_text', 'cta_link', 'features']

    def get_features(self, obj):
        return [{'icon': f.icon, 'title': f.title, 'description': f.description} for f in obj.features.all()]


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field     = 'slug'
    pagination_class = None

    def get_serializer_class(self):
        return ServiceDetailSerializer if self.action == 'retrieve' else ServiceSerializer

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True).prefetch_related('features')
        return qs.filter(is_featured=True) if flag(self.request.query_params, 'featured') else qs

    @action(detail=True, methods=['post'])
    def inquiry(self, request, slug=None):
        service = self.get_object()
        limited = rate_limited(request, 'service-inquiry')
        if limited:
            return limited
        form = ServiceInquiryForm(form_data(request, ServiceInquiryForm.Meta.fields, **user_defaults(request)))
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        inquiry = form.save(commit=False)
        inquiry.service = service
        inquiry.save()
        notify_service_inquiry(inquiry)
        return Response({'detail': 'Thank you! Our team will contact you shortly about this service.'},
                        status=status.HTTP_201_CREATED)


class ServingAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServingArea
        fields = ['id', 'city', 'slug', 'state', 'is_featured']


class ServingAreaDetailSerializer(ServingAreaSerializer):
    pincodes           = serializers.ListField(source='pincode_list', read_only=True)
    available_services = serializers.SerializerMethodField()

    class Meta(ServingAreaSerializer.Meta):
        fields = ServingAreaSerializer.Meta.fields + [
            'description', 'contact_phone', 'contact_email', 'address', 'pincodes',
            'map_embed', 'available_services']

    def get_available_services(self, obj):
        return ServiceAvailabilitySerializer(obj.available_services(), many=True).data


class ServingAreaViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field     = 'slug'
    pagination_class = None
    queryset         = ServingArea.objects.filter(is_active=True)

    def get_serializer_class(self):
        return ServingAreaDetailSerializer if self.action == 'retrieve' else ServingAreaSerializer

    @action(detail=False)
    def check(self, request):
        pincode = request.query_params.get('pincode', '').strip()
        if not pincode.isdigit() or len(pincode) != 6:
            return Response({'pincode': ['Enter a 6-digit pincode.']}, status=status.HTTP_400_BAD_REQUEST)
        areas = [a for a in self.get_queryset().filter(pincodes__contains=pincode) if pincode in a.pincode_list]
        return Response({
            'pincode':     pincode,
            'serviceable': bool(areas),
            'areas':       ServingAreaSerializer(areas, many=True).data,
        })


class FAQView(APIView):
    def get(self, request):
        def faq(f):
            return {'id': f.pk, 'question': f.question, 'answer': f.answer}

        groups = [{'name': c.name, 'slug': c.slug, 'icon': c.icon,
                   'faqs': [faq(f) for f in c.faqs.all() if f.is_active]}
                  for c in FAQCategory.objects.filter(is_active=True).prefetch_related('faqs')]
        other = [faq(f) for f in GeneralFAQ.objects.filter(is_active=True, category__isnull=True)]
        if other:
            groups.append({'name': 'General', 'slug': '', 'icon': 'ti-help-circle', 'faqs': other})
        return Response([g for g in groups if g['faqs']])


class FlatPageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FlatPage
        fields = ['title', 'slug', 'icon', 'updated_at']


class FlatPageDetailSerializer(FlatPageSerializer):
    class Meta(FlatPageSerializer.Meta):
        fields = FlatPageSerializer.Meta.fields + ['content']


class FlatPageViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field     = 'slug'
    pagination_class = None
    queryset         = FlatPage.objects.filter(is_active=True)

    def get_serializer_class(self):
        return FlatPageDetailSerializer if self.action == 'retrieve' else FlatPageSerializer
