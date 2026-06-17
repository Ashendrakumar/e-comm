from django.contrib import admin
from django.utils.html import format_html
from core.admin_mixins import ExportCsvMixin
from .models import (
    Service, ServiceFeature, ServiceInquiry,
    ServingArea, FlatPage, FAQCategory, GeneralFAQ,
)


class ServiceFeatureInline(admin.TabularInline):
    model  = ServiceFeature
    extra  = 1
    fields = ('icon', 'title', 'description', 'order')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display        = ('title', 'price_info', 'is_active', 'is_featured', 'order')
    list_editable       = ('is_active', 'is_featured', 'order')
    list_filter         = ('is_active', 'is_featured')
    search_fields       = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}
    inlines             = [ServiceFeatureInline]
    fieldsets = (
        ('Basics', {
            'fields': ('title', 'slug', 'icon', 'color', 'short_description', 'description')
        }),
        ('Media', {
            'fields': ('image', 'banner')
        }),
        ('Call To Action', {
            'fields': ('price_info', 'cta_text', 'cta_link')
        }),
        ('Display', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
    )


@admin.register(ServiceInquiry)
class ServiceInquiryAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display  = ('name', 'service', 'phone', 'city', 'status', 'created_at')
    list_filter   = ('status', 'service', 'created_at')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy  = 'created_at'
    actions         = ['export_as_csv']


@admin.register(ServingArea)
class ServingAreaAdmin(admin.ModelAdmin):
    list_display        = ('city', 'state', 'contact_phone', 'is_active', 'is_featured')
    list_editable       = ('is_active', 'is_featured')
    list_filter         = ('state', 'is_active', 'is_featured')
    search_fields       = ('city', 'pincodes')
    prepopulated_fields = {'slug': ('city',)}
    fieldsets = (
        ('Location', {'fields': ('city', 'slug', 'state', 'description')}),
        ('Contact', {'fields': ('contact_phone', 'contact_email', 'address', 'pincodes')}),
        ('Map & SEO', {'fields': ('map_embed', 'meta_title', 'meta_description')}),
        ('Display', {'fields': ('is_active', 'is_featured')}),
    )


@admin.register(FlatPage)
class FlatPageAdmin(admin.ModelAdmin):
    list_display        = ('title', 'slug', 'show_in_footer', 'is_active', 'order', 'updated_at')
    list_editable       = ('show_in_footer', 'is_active', 'order')
    search_fields       = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Content', {'fields': ('title', 'slug', 'icon', 'content')}),
        ('Display', {'fields': ('show_in_footer', 'is_active', 'order')}),
        ('SEO', {'classes': ('collapse',), 'fields': ('meta_title', 'meta_description', 'meta_keywords')}),
    )


class GeneralFAQInline(admin.TabularInline):
    model  = GeneralFAQ
    extra  = 1
    fields = ('question', 'answer', 'order', 'is_active')


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display        = ('name', 'order', 'is_active')
    list_editable       = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines             = [GeneralFAQInline]


@admin.register(GeneralFAQ)
class GeneralFAQAdmin(admin.ModelAdmin):
    list_display  = ('question', 'category', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter   = ('category', 'is_active')
    search_fields = ('question', 'answer')
