"""
Utility functions for voting system including device fingerprinting,
voter verification, and vote validation.
"""

import hashlib
import json
from datetime import datetime


def get_client_ip(request):
    """
    Get client IP address from request
    Handles proxies and forwarded IPs
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def generate_device_fingerprint(request):
    """
    Generate a browser fingerprint based on multiple factors.
    This is designed to be seamless and automatic for repeat voters.
    """
    components = {
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
        'timezone_offset': request.META.get('HTTP_TIMEZONE_OFFSET', ''),
    }

    fingerprint_string = json.dumps(components, sort_keys=True)
    fingerprint_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()

    return fingerprint_hash


def get_or_create_device_identifier(request, tracking_method='browser_fingerprint'):
    """
    Get a stable device identifier based on the configured tracking method.
    The identifier is derived automatically from the request and is used to
    prevent duplicate votes from the same device without interrupting the user.
    """
    ip_address = get_client_ip(request)

    if tracking_method == 'ip_address':
        return ip_address
    elif tracking_method == 'browser_fingerprint':
        return generate_device_fingerprint(request)
    elif tracking_method == 'combined':
        fingerprint = generate_device_fingerprint(request)
        return f"{fingerprint}_{ip_address}"
    elif tracking_method == 'cookie':
        device_cookie = request.COOKIES.get('voting_device_id')
        if device_cookie:
            return device_cookie
        return generate_device_fingerprint(request)
    else:
        return generate_device_fingerprint(request)


def verify_voter_authentication(request, campaign, voter_code, email=None):
    """
    Verify voter authentication for campaigns requiring voter list
    
    Returns: dict with keys:
    - authenticated: bool
    - voter: Voter object or None
    - message: str with reason if not authenticated
    """
    from voting.models import Voter
    
    try:
        voter = Voter.objects.select_related('voter_list').get(
            voter_code=voter_code,
            voter_list=campaign.voter_list
        )
        
        # Optionally verify email if provided
        if email and voter.email != email:
            return {
                'authenticated': False,
                'voter': None,
                'message': 'Email does not match voter code'
            }
        
        # Check if voter is already verified
        if voter.is_verified:
            return {
                'authenticated': True,
                'voter': voter,
                'message': 'Voter verified successfully'
            }
        
        return {
            'authenticated': True,
            'voter': voter,
            'message': 'Voter code valid, verification required'
        }
    
    except Voter.DoesNotExist:
        return {
            'authenticated': False,
            'voter': None,
            'message': 'Invalid voter code'
        }


def check_voter_already_voted(campaign, category, voter=None, device_identifier=None):
    """
    Check if a voter or device has already voted in a category.
    For authenticated voting this uses the voter record; for open voting it uses the device identifier.
    """
    from voting.models import Vote

    if voter:
        return Vote.objects.filter(
            campaign=campaign,
            category=category,
            voter=voter
        ).exists()

    if device_identifier:
        return Vote.objects.filter(
            campaign=campaign,
            category=category,
            device_fingerprint=device_identifier
        ).exists()

    return False


def can_vote(request, campaign, category, voter=None):
    """
    Comprehensive check to determine if a user/device can vote
    
    Returns: dict with keys:
    - can_vote: bool
    - message: str with reason
    - reason_code: str for categorizing the reason
    """
    from voting.models import Vote
    
    # Check if campaign is active
    if not campaign.is_active:
        return {
            'can_vote': False,
            'message': 'Voting is not currently active for this campaign',
            'reason_code': 'campaign_inactive'
        }
    
    # Authentication-based checks
    if campaign.voting_mode == 'authenticated':
        if not voter:
            return {
                'can_vote': False,
                'message': 'Voter authentication required',
                'reason_code': 'auth_required'
            }
        
        # Check if voter already voted
        if check_voter_already_voted(campaign, category, voter=voter):
            return {
                'can_vote': False,
                'message': 'You have already voted in this category',
                'reason_code': 'already_voted'
            }
    
    # Device-based checks for open voting
    else:  # open voting mode
        device_identifier = get_or_create_device_identifier(
            request,
            campaign.device_tracking_method
        )
        
        # Check if device already voted
        if check_voter_already_voted(campaign, category, device_identifier=device_identifier):
            return {
                'can_vote': False,
                'message': 'You have already voted in this category from this device',
                'reason_code': 'already_voted'
            }
    
    return {
        'can_vote': True,
        'message': 'You can vote',
        'reason_code': 'ok'
    }


def record_vote(campaign, category, candidate, request, voter=None):
    """
    Record a vote with appropriate tracking based on voting mode.
    This keeps the experience seamless by automatically capturing the device identity.
    """
    from voting.models import Vote

    try:
        vote_data = {
            'campaign': campaign,
            'category': category,
            'candidate': candidate,
        }

        if voter:
            vote_data['voter'] = voter
        else:
            device_identifier = get_or_create_device_identifier(
                request,
                campaign.device_tracking_method
            )
            vote_data['voter_ip'] = get_client_ip(request)
            vote_data['device_fingerprint'] = device_identifier

        vote = Vote.objects.create(**vote_data)

        return {
            'success': True,
            'vote': vote,
            'message': 'Vote recorded successfully'
        }
    
    except Exception as e:
        return {
            'success': False,
            'vote': None,
            'message': f'Error recording vote: {str(e)}'
        }
