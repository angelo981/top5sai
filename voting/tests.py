from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.utils import timezone
from datetime import timedelta
from .forms import VoterAuthenticationForm
from .models import VotingCampaign, VotingCategory, Candidate, Vote, Voter, VoterList
from .utils import get_or_create_device_identifier, check_voter_already_voted, verify_voter_authentication


class VotingCampaignTests(TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.campaign = VotingCampaign.objects.create(
            title='Test Campaign',
            description='Test Description',
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7)
        )
        
        self.category = VotingCategory.objects.create(
            campaign=self.campaign,
            name='Test Category'
        )
        
        self.candidate1 = Candidate.objects.create(
            category=self.category,
            name='Candidate 1'
        )
        
        self.candidate2 = Candidate.objects.create(
            category=self.category,
            name='Candidate 2'
        )
    
    def test_campaign_is_active(self):
        """Test if campaign is active"""
        self.assertTrue(self.campaign.is_active)
    
    def test_total_votes(self):
        """Test total votes count"""
        Vote.objects.create(
            campaign=self.campaign,
            category=self.category,
            candidate=self.candidate1,
            voter_ip='192.168.1.1'
        )
        self.assertEqual(self.campaign.total_votes, 1)
    
    def test_candidate_vote_count(self):
        """Test candidate vote count"""
        Vote.objects.create(
            campaign=self.campaign,
            category=self.category,
            candidate=self.candidate1,
            voter_ip='192.168.1.1'
        )
        self.assertEqual(self.candidate1.vote_count, 1)
    
    def test_duplicate_vote_prevention(self):
        """Test that duplicate votes are prevented"""
        Vote.objects.create(
            campaign=self.campaign,
            category=self.category,
            candidate=self.candidate1,
            voter_ip='192.168.1.1'
        )

        with self.assertRaises(Exception):
            Vote.objects.create(
                campaign=self.campaign,
                category=self.category,
                candidate=self.candidate2,
                voter_ip='192.168.1.1'
            )

    def test_device_identifier_prevents_duplicate_votes(self):
        """Test that the same device fingerprint is recognized for duplicate voting checks."""
        request = RequestFactory().get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        request.META['HTTP_ACCEPT_LANGUAGE'] = 'en-US,en;q=0.9'
        request.META['HTTP_ACCEPT_ENCODING'] = 'gzip, deflate'

        device_id = get_or_create_device_identifier(request, 'browser_fingerprint')
        Vote.objects.create(
            campaign=self.campaign,
            category=self.category,
            candidate=self.candidate1,
            device_fingerprint=device_id,
        )

        self.assertTrue(check_voter_already_voted(self.campaign, self.category, device_identifier=device_id))

    def test_voter_code_must_belong_to_campaign_voter_list(self):
        """A voter code should only work for the campaign that references its voter list."""
        voter_list = VoterList.objects.create(name='Primary List', description='Primary', csv_file=SimpleUploadedFile('voters.csv', b'email,voter_code\nuser@example.com,ABC123\n', content_type='text/csv'))
        Voter.objects.create(voter_list=voter_list, email='user@example.com', voter_code='ABC123')

        other_list = VoterList.objects.create(name='Secondary List', description='Secondary', csv_file=SimpleUploadedFile('voters.csv', b'email,voter_code\nother@example.com,XYZ999\n', content_type='text/csv'))
        Voter.objects.create(voter_list=other_list, email='other@example.com', voter_code='XYZ999')

        campaign = VotingCampaign.objects.create(
            title='Authenticated Campaign',
            description='Requires voter code',
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            voting_mode='authenticated',
            voter_list=voter_list,
        )

        request = RequestFactory().get('/')
        result = verify_voter_authentication(request, campaign, 'XYZ999')

        self.assertFalse(result['authenticated'])
        self.assertEqual(result['message'], 'Invalid voter code')

    def test_voter_auth_form_rejects_codes_outside_campaign_voter_list(self):
        """The authentication form should validate codes against the current campaign's voter list."""
        voter_list = VoterList.objects.create(name='Primary List', description='Primary', csv_file=SimpleUploadedFile('voters.csv', b'email,voter_code\nuser@example.com,ABC123\n', content_type='text/csv'))
        Voter.objects.create(voter_list=voter_list, email='user@example.com', voter_code='ABC123')

        campaign = VotingCampaign.objects.create(
            title='Authenticated Campaign',
            description='Requires voter code',
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            voting_mode='authenticated',
            voter_list=voter_list,
        )

        form = VoterAuthenticationForm({'voter_code': 'ABC123', 'email': 'user@example.com'}, campaign=campaign)

        self.assertTrue(form.is_valid())

        form = VoterAuthenticationForm({'voter_code': 'UNKNOWN', 'email': 'user@example.com'}, campaign=campaign)

        self.assertFalse(form.is_valid())
        self.assertIn('Invalid voter code', form.non_field_errors()[0])
