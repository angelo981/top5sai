from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from urllib.parse import parse_qs, urlparse


class Message(models.Model):
    """Model for storing contact form messages"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    service = models.CharField(
        max_length=100,
        choices=[
            ('Live Wedding', 'Live Wedding'),
            ('Live Streaming', 'Live Streaming'),
            ('Event Planning', 'Event Planning'),
            ('Photography', 'Photography'),
            ('Videography', 'Videography'),
            ('Other', 'Other'),
        ],
        default='Other'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.name} - {self.email}"


class AdminUser(models.Model):
    """Model for admin users"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Admin Users"

    def __str__(self):
        return f"{self.username} ({self.role})"


class BlogPost(models.Model):
    """A photo or YouTube video and description published on the activities blog."""
    photo = models.ImageField(upload_to='blog/photos/', blank=True)
    youtube_url = models.URLField(blank=True)
    description = models.TextField()
    event_date = models.DateField(blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog post'
        verbose_name_plural = 'Blog posts'

    def __str__(self):
        return f'Blog post {self.pk}'

    def clean(self):
        if not self.photo and not self.youtube_url:
            raise ValidationError('Add a photo or a YouTube link for this blog post.')

    @property
    def youtube_embed_url(self):
        if not self.youtube_url:
            return ''

        parsed_url = urlparse(self.youtube_url)
        if parsed_url.hostname in {'youtu.be', 'www.youtu.be'}:
            video_id = parsed_url.path.strip('/')
        elif parsed_url.hostname in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query).get('v', [''])[0]
            elif parsed_url.path.startswith('/embed/'):
                video_id = parsed_url.path.split('/embed/', 1)[1].split('/', 1)[0]
            else:
                video_id = ''
        else:
            video_id = ''

        return f'https://www.youtube.com/embed/{video_id}' if video_id else ''
