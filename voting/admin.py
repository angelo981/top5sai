from django.contrib import admin
from django.utils.html import format_html
from .models import (
    VotingCampaign, VotingCategory, Candidate, Vote, VoterList, Voter,
    CandidateAchievement, CandidateActivityPhoto, CandidateMedia
)
from .forms import VoterListUploadForm


class VotingCategoryInline(admin.TabularInline):
    model = VotingCategory
    extra = 1
    fields = ['name', 'description', 'order']


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1
    fields = ['name', 'description', 'photo', 'order']


class CandidateAchievementInline(admin.TabularInline):
    model = CandidateAchievement
    extra = 1
    fields = ['title', 'description', 'icon', 'order']


class CandidateActivityPhotoInline(admin.TabularInline):
    model = CandidateActivityPhoto
    extra = 1
    fields = ['photo', 'caption', 'activity_type', 'order']


class CandidateMediaInline(admin.TabularInline):
    model = CandidateMedia
    extra = 1
    fields = ['media_type', 'title', 'embed_url', 'video_file', 'order']


class VoterInline(admin.TabularInline):
    model = Voter
    extra = 0
    readonly_fields = ['voter_code', 'email', 'full_name', 'is_verified', 'created_at']
    can_delete = False
    fields = ['voter_code', 'email', 'full_name', 'is_verified', 'created_at']


@admin.register(VoterList)
class VoterListAdmin(admin.ModelAdmin):
    form = VoterListUploadForm
    list_display = ['name', 'total_voters', 'created_at', 'voter_count_display']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    inlines = [VoterInline]
    readonly_fields = ['total_voters', 'created_at', 'updated_at', 'voter_preview']
    fieldsets = (
        ('Voter List Information', {
            'fields': ('name', 'description')
        }),
        ('CSV Upload', {
            'fields': ('csv_file',),
            'description': 'Upload a CSV file with columns: email, voter_code, full_name (optional), and any additional identification fields.'
        }),
        ('Statistics', {
            'fields': ('total_voters', 'voter_preview'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def voter_preview(self, obj):
        """Display a preview of voters"""
        voters = obj.voters.all()[:10]
        if not voters:
            return "No voters yet"
        
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for voter in voters:
            html += f'<li>{voter.email} ({voter.voter_code})</li>'
        html += '</ul>'
        
        if obj.total_voters > 10:
            html += f'<p style="margin-top: 10px; color: #666;">... and {obj.total_voters - 10} more voters</p>'
        
        return format_html(html)
    voter_preview.short_description = "Voter Preview"
    
    def voter_count_display(self, obj):
        """Display voter count with color"""
        color = 'green' if obj.total_voters > 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.total_voters
        )
    voter_count_display.short_description = 'Voters'


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['voter_code', 'email', 'full_name', 'voter_list', 'is_verified', 'created_at']
    list_filter = ['voter_list', 'is_verified', 'created_at']
    search_fields = ['voter_code', 'email', 'full_name']
    readonly_fields = ['voter_code', 'email', 'voter_list', 'created_at']
    fields = ['voter_code', 'email', 'full_name', 'voter_list', 'is_verified', 'additional_info', 'created_at']
    
    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(VotingCampaign)
class VotingCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'status',
        'voting_mode_display',
        'start_date',
        'end_date',
        'total_votes',
        'results_visibility',
        'created_at'
    ]
    list_filter = [
        'status',
        'voting_mode',
        'start_date',
        'created_at',
        'results_visibility',
        'results_access'
    ]
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'
    inlines = [VotingCategoryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'short_description')
        }),
        ('Campaign Settings', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Media', {
            'fields': ('banner',)
        }),
        ('Voting Mode & Authentication', {
            'fields': ('voting_mode', 'voter_list'),
            'description': 'Choose between open voting (device-based tracking) or authenticated voting (voter list required).'
        }),
        ('Device Tracking Settings (Open Voting)', {
            'fields': ('device_tracking_method', 'enable_ip_restriction'),
            'classes': ('collapse',),
            'description': 'Configure how devices are tracked in open voting mode.'
        }),
        ('Results Visibility & Access', {
            'fields': ('show_live_results', 'results_visibility', 'results_access'),
            'description': 'Configure when and to whom voting results are visible.'
        }),
    )
    
    def voting_mode_display(self, obj):
        """Display voting mode with color"""
        colors = {
            'open': 'blue',
            'authenticated': 'green'
        }
        color = colors.get(obj.voting_mode, 'gray')
        label = 'Open' if obj.voting_mode == 'open' else 'Authenticated'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            label
        )
    voting_mode_display.short_description = 'Voting Mode'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter voter list choices based on voting mode"""
        if db_field.name == 'voter_list':
            kwargs['queryset'] = VoterList.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(VotingCategory)
class VotingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign', 'order', 'created_at']
    list_filter = ['campaign', 'created_at']
    search_fields = ['name', 'campaign__title']
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'vote_count', 'vote_percentage', 'order']
    list_filter = ['category__campaign', 'category', 'created_at']
    search_fields = ['name', 'category__name']
    readonly_fields = ['vote_count', 'vote_percentage', 'created_at']
    inlines = [CandidateAchievementInline, CandidateActivityPhotoInline, CandidateMediaInline]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'category', 'campaign', 'voter_ip', 'voted_at']
    list_filter = ['campaign', 'category', 'voted_at']
    search_fields = ['candidate__name', 'voter_ip']
    date_hierarchy = 'voted_at'
    readonly_fields = ['voted_at', 'voter_ip', 'campaign', 'category', 'candidate']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(CandidateAchievement)
class CandidateAchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'candidate', 'icon', 'order', 'created_at']
    list_filter = ['candidate__category__campaign', 'created_at']
    search_fields = ['title', 'candidate__name']
    ordering = ['candidate', 'order']


@admin.register(CandidateActivityPhoto)
class CandidateActivityPhotoAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'caption', 'activity_type', 'order', 'created_at']
    list_filter = ['activity_type', 'candidate__category__campaign', 'created_at']
    search_fields = ['caption', 'candidate__name']
    ordering = ['candidate', 'order']


@admin.register(CandidateMedia)
class CandidateMediaAdmin(admin.ModelAdmin):
    list_display = ['title', 'candidate', 'media_type', 'order', 'created_at']
    list_filter = ['media_type', 'candidate__category__campaign', 'created_at']
    search_fields = ['title', 'candidate__name']
    ordering = ['candidate', 'order']
    readonly_fields = ['youtube_video_id', 'tiktok_video_id']
