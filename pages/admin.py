from django.contrib import admin
from .models import Service, ServingArea


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
