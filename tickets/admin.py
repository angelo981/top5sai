from django.contrib import admin
from .models import Event, TicketCategory, TicketPurchase, Ticket


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'venue', 'start_datetime', 'end_datetime', 'is_active')
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity', 'sold')
    list_filter = ('event',)


@admin.register(TicketPurchase)
class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'quantity', 'total_price', 'status', 'buyer_phone', 'created_at')
    list_filter = ('status', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'purchase', 'is_validated', 'created_at')
    search_fields = ('code',)
