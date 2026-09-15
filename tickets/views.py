from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, Http404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Event, TicketCategory, TicketPurchase, Ticket
from .forms import PurchaseForm, ReserveTicketsForm
from .utils import initiate_mobile_money_payment, generate_ticket_qr, generate_premium_ticket_image, send_ticket_email
from io import BytesIO
import os
import uuid


def event_list(request):
    # Events listing has been removed from the public flow.
    # Redirect users to the first upcoming event detail instead.
    event = Event.objects.filter(is_active=True).order_by('start_datetime').first()
    if event:
        return redirect('tickets:event_detail', slug=event.slug)
    return redirect('home')


def first_event_redirect(request):
    """Redirect to the first upcoming active event detail page.

    Falls back to the event list if no active events are available.
    """
    event = Event.objects.filter(is_active=True).order_by('start_datetime').first()
    if event:
        return redirect('tickets:event_detail', slug=event.slug)
    return redirect('tickets:event_list')


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    categories = event.categories.all()
    category_prices = {str(category.id): category.price for category in categories}
    form = PurchaseForm(initial={})
    download_ticket_code = request.session.pop('download_ticket_code', None)
    ticket_confirmation = request.session.pop('ticket_confirmation', None)
    return render(request, 'tickets/event_detail.html', {
        'event': event,
        'categories': categories,
        'category_prices': category_prices,
        'form': form,
        'download_ticket_code': download_ticket_code,
        'show_download_button': bool(download_ticket_code),
        'ticket_confirmation': ticket_confirmation,
    })


def _set_ticket_confirmation(request, purchase, tickets):
    if not tickets:
        return
    ticket = tickets[0]
    request.session['download_ticket_code'] = str(ticket.code)
    request.session['ticket_confirmation'] = {
        'event_title': purchase.category.event.title,
        'event_slug': purchase.category.event.slug,
        'category': purchase.category.name,
        'quantity': purchase.quantity,
        'total_price': f"{purchase.total_price:.2f}",
        'ticket_code': str(ticket.code),
    }


def spinny_demo(request):
    """Render a demo ticket page inspired by the provided Spinny layout.

    Uses the first active event as sample data when available.
    """
    event = Event.objects.filter(is_active=True).order_by('start_datetime').first()
    categories = event.categories.all() if event else []
    category_prices = {str(category.id): category.price for category in categories} if categories else {}
    return render(request, 'tickets/spinny_ticket.html', {
        'event': event,
        'categories': categories,
        'category_prices': category_prices,
    })


def reserve_tickets(request):
    initial = {}
    selected_category = None
    selected_quantity = 1
    total_amount = None

    if request.method == 'GET':
        category_id = request.GET.get('category_id')
        quantity = request.GET.get('quantity', '1')
        phone_number = request.GET.get('phone_number', '')
        if category_id:
            selected_category = TicketCategory.objects.filter(id=category_id).first()
            if selected_category is None:
                event = Event.objects.filter(is_active=True).order_by('start_datetime').first()
                if event:
                    selected_category = event.categories.first()
            if selected_category:
                selected_quantity = int(quantity or 1)
                total_amount = selected_category.price * selected_quantity
                initial = {
                    'category_id': selected_category.id,
                    'quantity': selected_quantity,
                    'phone_number': phone_number,
                }
        else:
            event = Event.objects.filter(is_active=True).order_by('start_datetime').first()
            if event:
                selected_category = event.categories.first()
                if selected_category:
                    selected_quantity = int(quantity or 1)
                    total_amount = selected_category.price * selected_quantity
                    initial = {
                        'category_id': selected_category.id,
                        'quantity': selected_quantity,
                        'phone_number': phone_number,
                    }

        form = ReserveTicketsForm(initial=initial)
        return render(request, 'tickets/reserve_tickets.html', {
            'form': form,
            'event': selected_category.event if selected_category else None,
            'selected_category': selected_category,
            'selected_quantity': selected_quantity,
            'total_amount': total_amount,
        })

    form = ReserveTicketsForm(request.POST)
    if not form.is_valid():
        selected_category = None
        selected_quantity = 1
        total_amount = None
        category_id = request.POST.get('category_id')
        quantity = request.POST.get('quantity', '1')
        if category_id:
            selected_category = TicketCategory.objects.filter(id=category_id).first()
            if selected_category:
                selected_quantity = int(quantity or 1)
                total_amount = selected_category.price * selected_quantity
        return render(request, 'tickets/reserve_tickets.html', {
            'form': form,
            'event': selected_category.event if selected_category else None,
            'selected_category': selected_category,
            'selected_quantity': selected_quantity,
            'total_amount': total_amount,
        })

    category_id = form.cleaned_data['category_id']
    quantity = form.cleaned_data['quantity']
    phone = form.cleaned_data['phone_number']
    email = form.cleaned_data['email_address']
    payment_method = form.cleaned_data['payment_method']

    category = get_object_or_404(TicketCategory, id=category_id)
    if category.quantity - category.sold < quantity:
        messages.error(request, 'Not enough tickets available for this category.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    total = quantity * category.price
    purchase = TicketPurchase.objects.create(
        user=request.user if request.user.is_authenticated else None,
        category=category,
        quantity=quantity,
        total_price=total,
        buyer_phone=phone,
        buyer_email=email,
        status='pending'
    )

    purchase.status = 'paid'
    purchase.payment_ref = f"MOCK-{purchase.id}"
    purchase.save(update_fields=['status', 'payment_ref'])

    tickets = []
    for _ in range(quantity):
        ticket = Ticket.objects.create(purchase=purchase)
        generate_ticket_qr(ticket)
        tickets.append(ticket)

    category.sold += quantity
    category.save(update_fields=['sold'])

    send_ticket_email(tickets[0], request=request)
    _set_ticket_confirmation(request, purchase, tickets)

    messages.success(request, 'Reservation confirmed and your QR ticket has been generated.')
    return redirect('tickets:event_detail', slug=category.event.slug)


def payment_transaction(request, purchase_id):
    purchase = get_object_or_404(TicketPurchase, id=purchase_id)
    if purchase.status != 'paid':
        purchase.status = 'paid'
        purchase.payment_ref = f"MOCK-{purchase.id}"
        purchase.save(update_fields=['status', 'payment_ref'])

        tickets = []
        for _ in range(purchase.quantity):
            ticket = Ticket.objects.create(purchase=purchase)
            generate_ticket_qr(ticket)
            tickets.append(ticket)

        purchase.category.sold += purchase.quantity
        purchase.category.save(update_fields=['sold'])

        send_ticket_email(tickets[0], request=request)
        _set_ticket_confirmation(request, purchase, tickets)

    messages.success(request, 'Reservation confirmed and your QR ticket has been generated.')
    return redirect('tickets:event_detail', slug=purchase.category.event.slug)


def download_ticket(request, code):
    ticket = get_object_or_404(Ticket, code=code)
    if not ticket.qr_image:
        generate_ticket_qr(ticket)

    # Prefer the branded premium ticket image when available.
    premium_image_bytes = generate_premium_ticket_image(ticket)
    if premium_image_bytes:
        return FileResponse(BytesIO(premium_image_bytes), content_type='image/png', as_attachment=True, filename=f'ticket-{code}.png')

    if not ticket.qr_image:
        return redirect('tickets:event_list')

    image_path = ticket.qr_image.path if hasattr(ticket.qr_image, 'path') else None
    if not image_path or not os.path.exists(image_path):
        return redirect('tickets:event_list')
    return FileResponse(open(image_path, 'rb'), content_type='image/png', as_attachment=True, filename=f'ticket-{code}.png')


def purchase_ticket(request):
    if request.method != 'POST':
        return redirect('tickets:event_list')

    form = PurchaseForm(request.POST)
    if not form.is_valid():
        # Return JSON for AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Please correct the form errors.'}, status=400)
        messages.error(request, 'Please correct the form errors.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    category_id = form.cleaned_data['category_id']
    quantity = form.cleaned_data['quantity']
    phone = form.cleaned_data['phone_number']

    category = get_object_or_404(TicketCategory, id=category_id)
    if category.quantity - category.sold < quantity:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Not enough tickets available for this category.'}, status=400)
        messages.error(request, 'Not enough tickets available for this category.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    total = quantity * category.price
    purchase = TicketPurchase.objects.create(
        user=request.user if request.user.is_authenticated else None,
        category=category,
        quantity=quantity,
        total_price=total,
        buyer_phone=phone,
        status='pending'
    )

    # Initiate payment (stubbed)
    reference = str(uuid.uuid4())
    pay = initiate_mobile_money_payment('mtn_momo', float(total), phone, reference)

    # If payment provider returns a redirect URL (e.g., hosted payment page), return it to the client.
    payment_url = pay.get('payment_url')

    if pay.get('status') == 'success':
        purchase.status = 'paid'
        purchase.payment_ref = pay.get('transaction_id')
        purchase.save()

        # Reserve tickets and generate QR codes
        tickets = []
        for i in range(quantity):
            t = Ticket.objects.create(purchase=purchase)
            generate_ticket_qr(t)
            tickets.append(t)

        category.sold += quantity
        category.save(update_fields=['sold'])

        _set_ticket_confirmation(request, purchase, tickets)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'transaction_id': purchase.payment_ref, 'redirect': reverse('tickets:event_detail', args=[category.event.slug])})

        messages.success(request, 'Payment received — tickets issued.')
        return redirect(reverse('tickets:event_detail', args=[category.event.slug]))

    messages.error(request, 'Payment failed. Please try again.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff)
def admin_dashboard(request):
    events = Event.objects.all().order_by('-start_datetime')
    purchases = TicketPurchase.objects.order_by('-created_at')[:50]
    return render(request, 'tickets/admin_dashboard.html', {'events': events, 'purchases': purchases})


@user_passes_test(is_staff)
def validate_ticket(request):
    code = request.GET.get('code') or request.POST.get('code')
    ticket = None
    message = ''
    if code:
        try:
            ticket = Ticket.objects.get(code=code)
            if ticket.is_validated:
                message = 'Ticket already used.'
            else:
                ticket.is_validated = True
                ticket.save(update_fields=['is_validated'])
                message = 'Ticket validated successfully.'
        except Ticket.DoesNotExist:
            message = 'Ticket not found.'

    return render(request, 'tickets/validate.html', {'ticket': ticket, 'message': message})
