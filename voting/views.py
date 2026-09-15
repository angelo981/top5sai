from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Prefetch
from django.contrib import messages
from .models import VotingCampaign, VotingCategory, Candidate, Vote, Voter
from .utils import (
    get_client_ip,
    generate_device_fingerprint,
    get_or_create_device_identifier,
    verify_voter_authentication,
    check_voter_already_voted,
    can_vote,
    record_vote
)
from .forms import VoterAuthenticationForm


def campaign_list(request):
    """Display list of active voting campaigns"""
    campaigns = VotingCampaign.objects.filter(status='active').order_by('-start_date')
    return render(request, 'voting/campaign_list.html', {
        'campaigns': campaigns,
        'page': 'Voting',
        'now': timezone.now()
    })


def campaign_detail(request, pk):
    """Display campaign details with voting interface"""
    campaign = get_object_or_404(VotingCampaign, pk=pk, status='active')
    categories = campaign.categories.prefetch_related(
        Prefetch(
            'candidates',
            queryset=Candidate.objects.annotate(vote_total=Count('votes')).order_by('-vote_total', 'name')
        )
    ).all()
    
    # Authentication handling
    authenticated_voter = None
    show_voting_interface = True
    auth_form = None
    
    if campaign.voting_mode == 'authenticated':
        # Check if voter is authenticated in session
        authenticated_voter = request.session.get(f'voter_campaign_{pk}')
        
        if not authenticated_voter:
            show_voting_interface = False
            
            # Handle form submission
            if request.method == 'POST':
                form = VoterAuthenticationForm(request.POST, campaign=campaign)
                if form.is_valid():
                    voter_code = form.cleaned_data.get('voter_code')
                    email = form.cleaned_data.get('email')
                    
                    auth_result = verify_voter_authentication(
                        request,
                        campaign,
                        voter_code,
                        email
                    )
                    
                    if auth_result['authenticated']:
                        voter = auth_result['voter']
                        request.session[f'voter_campaign_{pk}'] = voter.id
                        request.session[f'voter_email_{pk}'] = voter.email
                        authenticated_voter = voter.id
                        show_voting_interface = True
                        messages.success(request, 'Voter verified successfully!')
                    else:
                        messages.error(request, auth_result['message'])
            else:
                form = VoterAuthenticationForm(campaign=campaign)
            
            auth_form = form
    else:
        # Open voting mode
        show_voting_interface = True
    
    # Get device identifier for open voting
    device_identifier = None
    if campaign.voting_mode == 'open':
        device_identifier = get_or_create_device_identifier(
            request,
            campaign.device_tracking_method
        )
    
    context = {
        'campaign': campaign,
        'categories': categories,
        'show_voting_interface': show_voting_interface,
        'authenticated_voter': authenticated_voter,
        'auth_form': auth_form,
        'device_identifier': device_identifier,
        'page': 'Voting'
    }
    
    return render(request, 'voting/campaign_detail.html', context)


@require_http_methods(["POST"])
def submit_vote(request, campaign_id, category_id):
    """Handle vote submission with support for both authenticated and open voting"""
    try:
        campaign = get_object_or_404(VotingCampaign, pk=campaign_id, status='active')
        category = get_object_or_404(VotingCategory, pk=category_id, campaign=campaign)
        candidate_id = request.POST.get('candidate_id')
        
        if not candidate_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Please select a candidate'
            }, status=400)
        
        candidate = get_object_or_404(Candidate, pk=candidate_id, category=category)
        
        # Determine voter based on campaign voting mode
        voter = None
        device_identifier = None
        
        if campaign.voting_mode == 'authenticated':
            # Get authenticated voter from session
            voter_id = request.session.get(f'voter_campaign_{campaign_id}')
            if not voter_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Voter authentication required'
                }, status=403)
            
            try:
                voter = Voter.objects.get(id=voter_id)
            except Voter.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Voter session expired'
                }, status=403)
        else:
            # Open voting mode - use device tracking
            device_identifier = get_or_create_device_identifier(
                request,
                campaign.device_tracking_method
            )
        
        # Check if user/device can vote
        vote_check = can_vote(request, campaign, category, voter=voter)
        if not vote_check['can_vote']:
            return JsonResponse({
                'status': 'error',
                'message': vote_check['message']
            }, status=400)
        
        # Record the vote
        vote_result = record_vote(campaign, category, candidate, request, voter=voter)
        
        if vote_result['success']:
            return JsonResponse({
                'status': 'success',
                'message': vote_result['message'],
                'vote_id': vote_result['vote'].id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': vote_result['message']
            }, status=500)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_results(request, campaign_id, category_id):
    """Get live voting results for a category"""
    try:
        campaign = get_object_or_404(VotingCampaign, pk=campaign_id)
        category = get_object_or_404(VotingCategory, pk=category_id, campaign=campaign)
        
        candidates = category.candidates.annotate(vote_total=Count('votes')).order_by('-vote_total', 'name')
        total_votes = Vote.objects.filter(campaign=campaign, category=category).count()
        
        results = []
        for candidate in candidates:
            percentage = 0
            if total_votes > 0:
                percentage = round((candidate.vote_total / total_votes) * 100, 2)
            results.append({
                'id': candidate.id,
                'name': candidate.name,
                'votes': candidate.vote_total,
                'percentage': percentage
            })
        
        return JsonResponse({
            'status': 'success',
            'total_votes': total_votes,
            'candidates': results
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def voting_results(request, pk):
    """Display voting results page with ranking and admin-controlled visibility"""
    campaign = get_object_or_404(VotingCampaign, pk=pk)
    
    # Check if results can be viewed
    can_view_results = campaign.can_view_results(request.user)
    
    context = {
        'campaign': campaign,
        'can_view_results': can_view_results,
        'page': 'Voting Results'
    }
    
    if can_view_results:
        # Get all categories and sort their candidates by vote count
        categories = campaign.categories.prefetch_related('candidates').all()
        total_votes = Vote.objects.filter(campaign=campaign).count()
        
        # Create a list of categories with pre-sorted candidates
        categories_with_sorted = []
        for category in categories:
            # Get candidates sorted by vote count (descending)
            candidates_list = sorted(
                category.candidates.all(),
                key=lambda x: x.vote_count,
                reverse=True
            )
            category.sorted_candidates = candidates_list
            categories_with_sorted.append(category)
        
        context.update({
            'categories': categories_with_sorted,
            'total_votes': total_votes,
            'categories_count': len(categories_with_sorted),
        })
    
    return render(request, 'voting/voting_results.html', context)


