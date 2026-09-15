from django.utils import timezone

from tickets.models import Event


def show_buy_tickets_link(request):
    has_open_event = Event.objects.filter(
        is_active=True,
        end_datetime__gte=timezone.now(),
    ).exists()
    return {'show_buy_tickets_link': has_open_event}
