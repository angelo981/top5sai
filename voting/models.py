from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import uuid


class VoterList(models.Model):
    """Model for managing voter lists"""
    name = models.CharField(max_length=255, help_text="Name of this voter list")
    description = models.TextField(blank=True, help_text="Description of the voter list")
    csv_file = models.FileField(upload_to='voting/voter_lists/', help_text="CSV file containing voter details")
    created_by = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_voters = models.PositiveIntegerField(default=0, help_text="Total number of voters in this list")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Voter Lists'
    
    def __str__(self):
        return f"{self.name} ({self.total_voters} voters)"


class Voter(models.Model):
    """Model for storing voter information"""
    voter_list = models.ForeignKey(VoterList, on_delete=models.CASCADE, related_name='voters')
    email = models.EmailField(help_text="Voter's email address")
    voter_code = models.CharField(max_length=100, unique=True, help_text="Unique voter code")
    full_name = models.CharField(max_length=255, blank=True, help_text="Voter's full name")
    additional_info = models.JSONField(default=dict, blank=True, help_text="Additional identification fields")
    is_verified = models.BooleanField(default=False, help_text="Whether voter has been verified")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['voter_code']
        unique_together = ('voter_list', 'email')
    
    def __str__(self):
        return f"{self.voter_code} - {self.email}"


class VotingCampaign(models.Model):
    """Model for voting campaigns"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    RESULTS_VISIBILITY_CHOICES = [
        ('hidden', 'Hidden - Results not visible'),
        ('during', 'During Voting - Visible while campaign is active'),
        ('after', 'After Voting - Visible only after campaign ends'),
        ('always', 'Always - Results always visible'),
    ]
    
    RESULTS_ACCESS_CHOICES = [
        ('everyone', 'Everyone'),
        ('authenticated', 'Authenticated Users Only'),
        ('admin', 'Administrators Only'),
    ]
    
    VOTING_MODE_CHOICES = [
        ('open', 'Open Voting - No authentication required'),
        ('authenticated', 'Authenticated - Voter list required'),
    ]
    
    DEVICE_TRACKING_CHOICES = [
        ('browser_fingerprint', 'Browser Fingerprinting'),
        ('ip_address', 'IP Address'),
        ('cookie', 'Cookie-based'),
        ('combined', 'Combined Methods'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    banner = models.ImageField(upload_to='voting/campaigns/banners/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Authentication settings
    voting_mode = models.CharField(
        max_length=20,
        choices=VOTING_MODE_CHOICES,
        default='open',
        help_text='Is authentication required for voting?'
    )
    voter_list = models.ForeignKey(
        VoterList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text='Associated voter list (required for authenticated voting)'
    )
    
    # Device tracking settings (for open voting mode)
    device_tracking_method = models.CharField(
        max_length=20,
        choices=DEVICE_TRACKING_CHOICES,
        default='browser_fingerprint',
        help_text='Method for tracking devices in open voting mode'
    )
    enable_ip_restriction = models.BooleanField(
        default=False,
        help_text='Restrict voting by IP address in open voting mode'
    )
    
    # Results visibility settings
    results_visibility = models.CharField(
        max_length=20, 
        choices=RESULTS_VISIBILITY_CHOICES, 
        default='after',
        help_text='When should voting results be visible?'
    )
    results_access = models.CharField(
        max_length=20,
        choices=RESULTS_ACCESS_CHOICES,
        default='everyone',
        help_text='Who can view the voting results?'
    )
    show_live_results = models.BooleanField(
        default=True,
        help_text='Show live vote counts during voting'
    )
    
    # Authentication messages
    auth_title = models.CharField(
        max_length=200,
        default='Verify Your Identity',
        help_text='Title for voter authentication section'
    )
    auth_message = models.TextField(
        default='Please authenticate with your voter credentials to participate in this election.',
        help_text='Instructions for voter authentication'
    )
    auth_help_text = models.TextField(
        default='If you don\'t have your voter code or have issues authenticating, please contact the election administrator.',
        help_text='Help text shown below the authentication form'
    )
    
    # Authentication form labels
    voter_code_label = models.CharField(
        max_length=100,
        default='Voter Code',
        help_text='Label for voter code field'
    )
    voter_email_label = models.CharField(
        max_length=100,
        default='Email Address',
        help_text='Label for email field'
    )
    auth_submit_label = models.CharField(
        max_length=100,
        default='Verify & Proceed to Voting',
        help_text='Label for authentication submit button'
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Voting Campaign'
        verbose_name_plural = 'Voting Campaigns'
    
    def __str__(self):
        return self.title
    
    def can_view_results(self, user=None):
        """Check if results can be viewed based on visibility settings"""
        now = timezone.now()
        
        # Check visibility timing
        if self.results_visibility == 'hidden':
            return False
        elif self.results_visibility == 'during':
            if not (self.start_date <= now <= self.end_date):
                return False
        elif self.results_visibility == 'after':
            if now <= self.end_date:
                return False
        # 'always' - always visible
        
        # Check access permissions
        if self.results_access == 'admin':
            return user and user.is_staff
        elif self.results_access == 'authenticated':
            return user and user.is_authenticated
        # 'everyone' - everyone can view
        
        return True
    
    @property
    def is_active(self):
        """Check if campaign is currently active"""
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date
    
    @property
    def total_votes(self):
        """Get total number of votes in this campaign"""
        return Vote.objects.filter(campaign=self).count()
    
    @property
    def days_remaining(self):
        """Get days remaining until campaign ends"""
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0


class VotingCategory(models.Model):
    """Model for voting categories within campaigns"""
    campaign = models.ForeignKey(VotingCampaign, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Voting Categories'
    
    def __str__(self):
        return f"{self.campaign.title} - {self.name}"


class Candidate(models.Model):
    """Model for voting candidates"""
    category = models.ForeignKey(VotingCategory, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='voting/candidates/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def vote_count(self):
        """Get number of votes for this candidate"""
        return Vote.objects.filter(candidate=self).count()
    
    @property
    def vote_percentage(self):
        """Get percentage of votes"""
        category_votes = Vote.objects.filter(category=self.category).count()
        if category_votes == 0:
            return 0
        return round((self.vote_count / category_votes) * 100, 2)


class Vote(models.Model):
    """Model for recording votes"""
    campaign = models.ForeignKey(VotingCampaign, on_delete=models.CASCADE, related_name='votes')
    category = models.ForeignKey(VotingCategory, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')

    # Support for both authenticated and non-authenticated voting
    voter = models.ForeignKey(
        Voter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='votes',
        help_text='Voter record (for authenticated voting)'
    )
    voter_ip = models.GenericIPAddressField(null=True, blank=True)
    device_fingerprint = models.CharField(
        max_length=255,
        blank=True,
        help_text='Device fingerprint (for open voting mode)'
    )

    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-voted_at']

    def clean(self):
        super().clean()
        if not self.campaign or not self.category:
            return

        qs = Vote.objects.filter(campaign=self.campaign, category=self.category)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if self.voter:
            if qs.filter(voter=self.voter).exists():
                raise ValidationError('This voter has already voted in this category.')
        elif self.device_fingerprint:
            if qs.filter(device_fingerprint=self.device_fingerprint).exists():
                raise ValidationError('This device has already voted in this category.')
        elif self.voter_ip:
            if qs.filter(voter_ip=self.voter_ip).exists():
                raise ValidationError('This IP address has already voted in this category.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        if self.voter:
            return f"{self.candidate.name} - {self.voter.email}"
        return f"{self.candidate.name} - {self.voter_ip}"


class CandidateAchievement(models.Model):
    """Model for storing candidate achievements and accomplishments"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255, help_text="Title of the achievement")
    description = models.TextField(help_text="Description of the achievement")
    icon = models.CharField(
        max_length=50,
        default='fa-star',
        help_text="FontAwesome icon class (e.g., fa-star, fa-trophy, fa-medal)"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Candidate Achievements'
    
    def __str__(self):
        return f"{self.candidate.name} - {self.title}"


class CandidateActivityPhoto(models.Model):
    """Model for storing candidate activity photos in gallery"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='activity_photos')
    photo = models.ImageField(
        upload_to='voting/candidates/activities/',
        help_text="Activity photo"
    )
    caption = models.CharField(
        max_length=300,
        blank=True,
        help_text="Photo caption (e.g., 'Community event', 'Project completion')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the activity"
    )
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('event', 'Community Event'),
            ('project', 'Project/Work'),
            ('achievement', 'Achievement'),
            ('initiative', 'Initiative'),
            ('other', 'Other'),
        ],
        default='event',
        help_text="Type of activity"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order in gallery")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Candidate Activity Photos'
    
    def __str__(self):
        return f"{self.candidate.name} - {self.caption or 'Activity Photo'}"


class CandidateMedia(models.Model):
    """Model for storing candidate video links and embeddings"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='media_links')
    MEDIA_TYPE_CHOICES = [
        ('youtube', 'YouTube Video'),
        ('tiktok', 'TikTok Video'),
        ('video_file', 'Video File Upload'),
        ('other', 'Other Video Link'),
    ]
    
    media_type = models.CharField(
        max_length=50,
        choices=MEDIA_TYPE_CHOICES,
        default='youtube',
        help_text="Type of media"
    )
    title = models.CharField(max_length=255, help_text="Title of the video/media")
    description = models.TextField(blank=True, help_text="Description of the video/media")
    
    # For embedded links (YouTube, TikTok, etc.)
    embed_url = models.URLField(
        blank=True,
        help_text="URL to the video (YouTube link, TikTok link, etc.)"
    )
    
    # For direct video file uploads
    video_file = models.FileField(
        upload_to='voting/candidates/videos/',
        blank=True,
        help_text="Video file upload (MP4, WebM, etc.)"
    )
    
    # For YouTube embed ID extraction
    youtube_video_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="YouTube video ID (auto-extracted)"
    )
    
    # For TikTok embed ID extraction
    tiktok_video_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="TikTok video ID (auto-extracted)"
    )
    
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Candidate Media'
    
    def __str__(self):
        return f"{self.candidate.name} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Extract video IDs from URLs before saving"""
        if self.media_type == 'youtube' and self.embed_url and not self.youtube_video_id:
            # Extract YouTube video ID
            import re
            youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            if re.match(youtube_regex, self.embed_url):
                if 'youtu.be' in self.embed_url:
                    self.youtube_video_id = self.embed_url.split('/')[-1].split('?')[0]
                else:
                    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)', self.embed_url)
                    if match:
                        self.youtube_video_id = match.group(1)
        
        if self.media_type == 'tiktok' and self.embed_url and not self.tiktok_video_id:
            # Extract TikTok video ID
            import re
            match = re.search(r'(?:tiktok\.com/@[\w\.\-]+/video/)(\d+)', self.embed_url)
            if match:
                self.tiktok_video_id = match.group(1)
        
        super().save(*args, **kwargs)
