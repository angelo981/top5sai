from django.contrib import admin
from .models import BlogPost, Message, AdminUser


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('photo_preview', 'video_link', 'description_preview', 'event_date', 'venue', 'created_at')
    list_filter = ('event_date', 'created_at')
    search_fields = ('description', 'venue')
    readonly_fields = ('created_at',)

    @admin.display(description='Photo')
    def photo_preview(self, obj):
        return obj.photo.name or '-'

    @admin.display(description='YouTube link')
    def video_link(self, obj):
        return obj.youtube_url or '-'

    @admin.display(description='Description')
    def description_preview(self, obj):
        return obj.description[:80]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'service', 'is_read', 'created_at')
    list_filter = ('is_read', 'service', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('service', 'message', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'status', 'created_at')
    list_filter = ('role', 'status', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Login Information', {
            'fields': ('username', 'password', 'email')
        }),
        ('Permissions', {
            'fields': ('role', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
