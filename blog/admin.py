from django.contrib import admin
from django.utils.html import format_html
from .models import BlogCategory, BlogPost, BlogComment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display       = ('name', 'post_count', 'is_active', 'order')
    list_editable      = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields      = ('name',)


class BlogCommentInline(admin.TabularInline):
    model           = BlogComment
    extra           = 0
    fields          = ('name', 'email', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display        = ('title', 'category', 'status', 'is_featured', 'views_count', 'published_at')
    list_filter         = ('status', 'is_featured', 'category', 'created_at')
    list_editable       = ('status', 'is_featured')
    search_fields       = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy      = 'published_at'
    readonly_fields     = ('views_count', 'created_at', 'updated_at', 'preview_image')
    inlines             = [BlogCommentInline]
    autocomplete_fields = ('category',)
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'tags', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'preview_image')
        }),
        ('Author & Publishing', {
            'fields': ('author', 'author_name', 'status', 'is_featured', 'allow_comments', 'published_at')
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Stats', {
            'classes': ('collapse',),
            'fields': ('views_count', 'reading_minutes', 'created_at', 'updated_at')
        }),
    )

    def preview_image(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height:160px;border-radius:8px;" />', obj.featured_image.url)
        return '—'
    preview_image.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'post', 'is_approved', 'created_at')
    list_filter   = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('name', 'email', 'content')
    actions       = ['approve_comments']

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comment(s) approved.')
