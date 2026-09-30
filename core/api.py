"""Site-wide endpoints under /api/v1/ (mobile app).

    GET  /home/           everything the app's home screen shows, in one call
    GET  /config/         store details, social links, footer pages, choice lists
    GET  /banners/        ?type=hero|promo|category|sidebar
    GET  /testimonials/
    POST /contact/        {name, email, phone?, subject, message, inquiry_type?}
    POST /newsletter/     {email}
"""
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from pages.models import FlatPage, Service, ServingArea
from products.models import Product
from .api_utils import form_data, form_errors, rate_limited, user_defaults
from .forms import ContactForm, NewsletterForm
from .models import Banner, ContactInquiry, NewsletterSubscription, SiteSettings, SocialLink, Testimonial
from .views import home_display_lists, notify_contact_inquiry


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Banner
        fields = ['id', 'title', 'subtitle', 'image', 'mobile_image', 'link', 'button_text',
                  'banner_type', 'badge_text']


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Testimonial
        fields = ['id', 'name', 'designation', 'avatar', 'content', 'rating']


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Banner.objects.filter(is_active=True)
        kind = self.request.query_params.get('type')
        return qs.filter(banner_type=kind) if kind else qs


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TestimonialSerializer
    pagination_class = None
    queryset         = Testimonial.objects.filter(is_active=True)


class HomeView(APIView):
    def get(self, request):
        from pages.api import ServiceSerializer, ServingAreaSerializer
        from products.api import product_queryset
        from products.serializers import BrandSerializer, CategorySerializer, ProductListSerializer

        ctx   = {'request': request}
        lists = home_display_lists()
        cards = product_queryset()

        def products(qs):
            return ProductListSerializer(qs[:8], many=True, context=ctx).data

        return Response({
            'hero_banners':        BannerSerializer(lists['hero_banners'], many=True, context=ctx).data,
            'promo_banners':       BannerSerializer(lists['promo_banners'], many=True, context=ctx).data,
            'featured_categories': CategorySerializer(lists['featured_categories'], many=True, context=ctx).data,
            'featured_brands':     BrandSerializer(lists['featured_brands'], many=True, context=ctx).data,
            'featured_products':   products(cards.filter(is_featured=True)),
            'trending_products':   products(cards.filter(is_trending=True)),
            'new_arrivals':        products(cards.filter(is_new_arrival=True).order_by('-created_at')),
            'deals':               products(cards.filter(sale_price__isnull=False, stock__gt=0)
                                            .order_by('-updated_at')),
            'services':            ServiceSerializer(Service.objects.filter(is_active=True)[:6],
                                                     many=True, context=ctx).data,
            'serving_areas':       ServingAreaSerializer(ServingArea.objects.filter(is_active=True)
                                                         .order_by('-is_featured', 'city')[:10],
                                                         many=True, context=ctx).data,
            'testimonials':        TestimonialSerializer(lists['testimonials'], many=True, context=ctx).data,
            'why_choose_us':       [{'icon': w.icon, 'title': w.title, 'description': w.description}
                                    for w in lists['why_choose_us']],
        })


class ConfigView(APIView):
    """Store details and the fixed choice lists the app builds its forms and filters from."""

    def get(self, request):
        s = SiteSettings.get_settings()

        def url(f):
            return request.build_absolute_uri(f.url) if f else None

        def choices(pairs):
            return [{'value': v, 'label': label} for v, label in pairs]

        return Response({
            'store': {
                'name': s.site_name, 'tagline': s.tagline, 'logo': url(s.logo), 'favicon': url(s.favicon),
                'phone': s.phone, 'whatsapp': s.whatsapp, 'email': s.email, 'address': s.address,
                'working_hours': s.working_hours,
            },
            'social_links': [{'platform': link.platform, 'label': link.get_platform_display(), 'url': link.url}
                             for link in SocialLink.objects.filter(is_active=True)],
            'pages': [{'title': p.title, 'slug': p.slug, 'icon': p.icon}
                      for p in FlatPage.objects.filter(is_active=True, show_in_footer=True)],
            'choices': {
                'product_condition':    choices(Product.CONDITION_CHOICES),
                'product_ordering':     choices([('-created_at', 'Newest'), ('price', 'Price: low to high'),
                                                 ('-price', 'Price: high to low'), ('-views_count', 'Popular'),
                                                 ('-avg_rating', 'Top rated'), ('name', 'Name A–Z')]),
                'contact_inquiry_type': choices(ContactInquiry.INQUIRY_TYPE_CHOICES),
                'banner_type':          choices(Banner.BANNER_TYPE_CHOICES),
            },
        })


class ContactView(APIView):
    def post(self, request):
        limited = rate_limited(request, 'contact')
        if limited:
            return limited
        form = ContactForm(form_data(request, ContactForm.Meta.fields, **user_defaults(request)))
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        notify_contact_inquiry(form.save())
        return Response({'detail': 'Thank you! We will get back to you shortly.'}, status=status.HTTP_201_CREATED)


class NewsletterView(APIView):
    def post(self, request):
        limited = rate_limited(request, 'newsletter')
        if limited:
            return limited
        form = NewsletterForm({'email': request.data.get('email', '')})
        if not form.is_valid():
            return Response(form_errors(form), status=status.HTTP_400_BAD_REQUEST)
        sub, created = NewsletterSubscription.objects.get_or_create(email=form.cleaned_data['email'])
        if not created and not sub.is_active:
            sub.is_active = True
            sub.save(update_fields=['is_active'])
        return Response({'detail': 'Successfully subscribed to our newsletter!' if created
                         else 'You are already subscribed!'},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
