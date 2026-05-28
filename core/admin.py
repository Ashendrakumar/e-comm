from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, Banner, Testimonial, NewsletterSubscription, SocialLink, WhyChooseUs, ContactInquiry, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Branding', {'fields': ('site_name', 'tagline', 'logo', 'favicon')}),
        ('Contact', {'fields': ('phone', 'whatsapp', 'email', 'address', 'working_hours')}),
        ('Maps', {'fields': ('google_maps_embed',)}),
        ('SEO', {'fields': ('meta_description', 'meta_keywords', 'google_analytics_id')}),
    )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview', 'is_featured', 'is_active', 'order')
    list_editable = ('is_featured', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_featured', 'is_active')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:30px;">', obj.logo.url)
        return '—'
    logo_preview.short_description = 'Logo'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner_type', 'is_active', 'order', 'image_preview')
    list_editable = ('is_active', 'order')
    list_filter = ('banner_type', 'is_active')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;">', obj.image.url)
        return '—'
    image_preview.short_description = 'Preview'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'rating', 'is_active', 'order')
    list_editable = ('is_active', 'order')


@admin.register(WhyChooseUs)
class WhyChooseUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_active', 'order')
    list_editable = ('is_active', 'order')


@admin.register(NewsletterSubscription)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active',)
    readonly_fields = ('subscribed_at',)


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'inquiry_type', 'status', 'created_at')
    list_filter = ('status', 'inquiry_type')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'is_active', 'order')
    list_editable = ('is_active', 'order')
