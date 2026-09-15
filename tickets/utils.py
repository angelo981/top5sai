import os
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from io import BytesIO

# qrcode and Pillow are optional; gracefully degrade if missing
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except Exception:
    qrcode = None
    Image = None
    QR_AVAILABLE = False
    # qrcode or Pillow not available; QR generation will be skipped at runtime


def generate_ticket_qr(ticket):
    """Generate QR code image for a Ticket instance and save to MEDIA_ROOT."""
    code = str(ticket.code)
    if not QR_AVAILABLE:
        # Skip QR image generation but persist ticket record
        logging.getLogger(__name__).warning('Skipping QR generation for ticket %s (qrcode/Pillow missing)', code)
        ticket.qr_image = ''
        ticket.save(update_fields=['qr_image'])
        return ''

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    # Ensure directory exists
    media_dir = os.path.join(settings.MEDIA_ROOT, 'tickets', 'qrcodes')
    os.makedirs(media_dir, exist_ok=True)

    filename = f"{code}.png"
    path = os.path.join(media_dir, filename)
    img.save(path)

    # Save relative path for ImageField
    rel_path = os.path.join('tickets', 'qrcodes', filename)
    ticket.qr_image = rel_path
    ticket.save(update_fields=['qr_image'])
    return rel_path


def generate_premium_ticket_image(ticket):
    """Render a premium ticket card to a PNG image with the event photo and detailed booking info."""
    if not QR_AVAILABLE or Image is None or qrcode is None:
        return None

    event = ticket.purchase.category.event
    category = ticket.purchase.category
    purchase = ticket.purchase

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(str(ticket.code))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')

    canvas = Image.new('RGB', (1080, 1600), '#f5f7fb')

    if Image is not None:
        from PIL import ImageDraw, ImageFont

        draw_obj = ImageDraw.Draw(canvas)

        try:
            title_font = ImageFont.truetype('arial.ttf', 34)
            subtitle_font = ImageFont.truetype('arial.ttf', 22)
            body_font = ImageFont.truetype('arial.ttf', 20)
            small_font = ImageFont.truetype('arial.ttf', 16)
            bold_font = ImageFont.truetype('arial.ttf', 22)
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            bold_font = ImageFont.load_default()

        # Header bar
        draw_obj.rounded_rectangle((40, 40, 1040, 260), radius=30, fill='#0f172a')
        draw_obj.text((70, 80), 'TOP5SAI', fill='#fbbf24', font=bold_font)
        draw_obj.text((70, 120), 'Premium Entry Ticket', fill='#ffffff', font=subtitle_font)
        draw_obj.text((70, 165), event.title[:44], fill='#f8fafc', font=title_font)

        # Event photo/banner if available
        hero_image = None
        if event.banner:
            try:
                hero_image = Image.open(event.banner.path).convert('RGB')
            except Exception:
                hero_image = None

        if hero_image is not None:
            hero_image = hero_image.resize((1000, 360))
            hero_box = (40, 300, 1040, 660)
            draw_obj.rounded_rectangle(hero_box, radius=28, fill='#e2e8f0')
            canvas.paste(hero_image, (40, 300))
        else:
            draw_obj.rounded_rectangle((40, 300, 1040, 660), radius=28, fill='#e2e8f0')
            draw_obj.text((70, 430), 'Event photo unavailable', fill='#64748b', font=body_font)

        # Details card
        draw_obj.rounded_rectangle((50, 720, 1030, 1160), radius=28, fill='#ffffff', outline='#dbeafe')
        detail_y = 760
        details = [
            ('Event', event.title),
            ('Category', category.name),
            ('Quantity', str(purchase.quantity)),
            ('Price', f'{category.price:.2f} RWF'),
            ('Phone', purchase.buyer_phone or 'N/A'),
            ('Venue', event.venue or 'TBA'),
            ('Date', event.start_datetime.strftime('%d %b %Y %H:%M') if event.start_datetime else 'TBA'),
        ]
        for label, value in details:
            draw_obj.text((80, detail_y), label, fill='#475569', font=small_font)
            draw_obj.text((260, detail_y), value, fill='#0f172a', font=body_font)
            detail_y += 56

        # QR section
        draw_obj.rounded_rectangle((50, 1220, 1030, 1520), radius=28, fill='#f8fafc', outline='#dbeafe')
        canvas.paste(qr_img.resize((260, 260)), (120, 1260))
        draw_obj.text((430, 1280), 'Scan at entry', fill='#0f172a', font=bold_font)
        draw_obj.text((430, 1330), f'Ticket code: {ticket.code}', fill='#475569', font=body_font)
        draw_obj.text((430, 1380), 'Please present this ticket at the venue.', fill='#64748b', font=small_font)

        # Footer accent
        draw_obj.rounded_rectangle((50, 1540, 1030, 1585), radius=24, fill='#f59e0b')
        draw_obj.text((80, 1553), 'Thank you for attending', fill='#ffffff', font=body_font)

        buffer = BytesIO()
        canvas.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    return None


def send_ticket_email(ticket, request=None):
    """Send a premium ticket email to the buyer with a downloadable QR ticket attachment."""
    purchase = ticket.purchase
    email = purchase.buyer_email
    if not email:
        return None

    ticket_image_bytes = generate_premium_ticket_image(ticket)
    attachment_name = f"ticket-{ticket.code}.png"
    html_content = render_to_string('tickets/ticket_email.html', {
        'ticket': ticket,
        'purchase': purchase,
        'event': purchase.category.event,
        'category': purchase.category,
        'attachment_name': attachment_name,
        'request': request,
    })
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject=f"Your ticket for {purchase.category.event.title}",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.attach_alternative(html_content, 'text/html')
    if ticket_image_bytes:
        msg.attach(attachment_name, ticket_image_bytes, 'image/png')
    msg.send()
    return msg


def initiate_mobile_money_payment(provider, amount, phone, reference):
    """
    Stub for initiating a mobile-money payment. Replace with real API integration.
    Returns a dict with keys: status ('success'|'error'), transaction_id
    """
    # For development we simulate immediate success.
    return {
        'status': 'success',
        'transaction_id': reference or f"MOCK-{phone}-{amount}"
    }
