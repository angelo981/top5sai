from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Event(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.CharField(max_length=100, default="General", blank=True)
    banner = models.ImageField(upload_to='tickets/banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=255, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TicketCategory(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    sold = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (('event', 'name'),)

    @property
    def remaining_tickets(self):
        return max(self.quantity - self.sold, 0)

    def __str__(self):
        return f"{self.event.title} — {self.name}"


class TicketPurchase(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    payment_ref = models.CharField(max_length=128, blank=True)
    buyer_phone = models.CharField(max_length=32, blank=True)
    buyer_email = models.EmailField(max_length=254, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase {self.id} — {self.category.name} x{self.quantity} ({self.status})"


class Ticket(models.Model):
    purchase = models.ForeignKey(TicketPurchase, related_name='tickets', on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_image = models.ImageField(upload_to='tickets/qrcodes/', blank=True, null=True)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.code)
