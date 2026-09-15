from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import json

from .models import BlogPost, Message
from voting.models import VotingCampaign


def home(request):
    """Home page view"""
    # Get active voting campaigns
    now = timezone.now()
    active_campaigns = VotingCampaign.objects.filter(
        status='active',
        start_date__lte=now,
        end_date__gte=now
    ).order_by('-start_date')
    
    return render(request, 'myapp/home.html', {
        'page': 'Home',
        'active_campaigns': active_campaigns
    })


def about(request):
    """About page view"""
    return render(request, 'myapp/about.html', {'page': 'About'})


def service(request):
    """Service page view"""
    return render(request, 'myapp/service.html', {'page': 'Services'})


def portfolio(request):
    """Portfolio page view"""
    return render(request, 'myapp/portfolio.html', {'page': 'Portfolio'})


def blogs(request):
    """Blogs page view"""
    blog_posts = BlogPost.objects.all()
    return render(request, 'myapp/blogs.html', {
        'page': 'Blogs',
        'blog_posts': blog_posts,
    })


def partners(request):
    """Partners page view"""
    return render(request, 'myapp/partners.html', {'page': 'Partners'})


def contact(request):
    """Contact page view"""
    return render(request, 'myapp/contact.html', {'page': 'Contact'})


@require_http_methods(["POST"])
def submit_message(request):
    """Handle contact form submission"""
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('mail', '').strip()
        phone = request.POST.get('mobile', '').strip()
        service = request.POST.get('service', 'Other').strip()
        message = request.POST.get('message', '').strip()

        # Validate required fields
        if not all([name, email, message]):
            return JsonResponse({
                'status': 'error',
                'message': 'Please fill in all required fields'
            }, status=400)

        # Create message object
        msg = Message.objects.create(
            name=name,
            email=email,
            phone=phone,
            service=service,
            message=message
        )

        # Try to send email notification (optional)
        try:
            send_mail(
                subject=f'New Contact Form Submission from {name}',
                message=f"""
                Name: {name}
                Email: {email}
                Phone: {phone}
                Service: {service}
                
                Message:
                {message}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email sending failed: {str(e)}")

        return JsonResponse({
            'status': 'success',
            'message': 'Message sent successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)
