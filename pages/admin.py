from django.contrib import admin
from django.utils.html import format_html
from .models import Service, ServingArea, HomepageBanner, HomepageSection


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ServingArea)
class ServingAreaAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'is_active', 'is_featured')
    list_editable = ('is_active', 'is_featured')
    prepopulated_fields = {'slug': ('city',)}


@admin.register(HomepageBanner)
class HomepageBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', '_preview')
    list_editable = ('is_active', 'order')
    readonly_fields = ('created_at', 'updated_at', '_preview')
    fieldsets = (
        ('Content', {'fields': ('title', 'subtitle', 'link', 'link_text')}),
        ('Images', {'fields': ('image', 'image_mobile', '_preview')}),
        ('Badge', {'fields': ('badge_text', 'badge_color')}),
        ('Status', {'fields': ('is_active', 'order', 'created_at', 'updated_at')}),
    )

    def _preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="auto" style="border-radius: 4px;" />',
                obj.image.url
            )
        return 'No image'
    _preview.short_description = 'Preview'


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'section_type', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('section_type', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Identity', {'fields': ('name', 'section_type')}),
        ('Content', {'fields': ('title', 'subtitle', 'content'), 'classes': ('wide',)}),
        ('Display', {'fields': ('template', 'is_active', 'order')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'content':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    class Media:
        js = ('js/admin_draggable.js',)

