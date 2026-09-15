"""
Forms for voting system including voter authentication,
voter list upload, and voting forms.
"""

from django import forms
from django.core.exceptions import ValidationError
import csv
import io

from voting.models import VoterList, Voter, VotingCampaign


class VoterAuthenticationForm(forms.Form):
    """Form for voter authentication"""

    def __init__(self, *args, campaign=None, **kwargs):
        self.campaign = campaign
        super().__init__(*args, **kwargs)
    
    voter_code = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your voter code',
            'required': 'required'
        }),
        label='Voter Code'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email (optional)',
        }),
        label='Email Address'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        voter_code = cleaned_data.get('voter_code')

        if voter_code:
            queryset = Voter.objects.filter(voter_code=voter_code)
            if self.campaign and self.campaign.voter_list_id:
                queryset = queryset.filter(voter_list=self.campaign.voter_list)
            elif self.campaign and not self.campaign.voter_list_id:
                raise ValidationError('This campaign is not configured with a voter list.')

            if not queryset.exists():
                raise ValidationError('Invalid voter code. Please check and try again.')
        
        return cleaned_data


class VoterListUploadForm(forms.ModelForm):
    """Form for uploading voter lists"""
    
    class Meta:
        model = VoterList
        fields = ['name', 'description', 'csv_file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of the voter list',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of the voter list'
            }),
            'csv_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv'
            })
        }
    
    def clean_csv_file(self):
        """Validate CSV file format"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file:
            return csv_file
        
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('Please upload a CSV file.')
        
        # Read and validate CSV structure
        try:
            content = csv_file.read().decode('utf-8')
            csv_file.seek(0)  # Reset file pointer
            
            reader = csv.DictReader(io.StringIO(content))
            
            # Check required columns
            if not reader.fieldnames:
                raise ValidationError('CSV file is empty.')
            
            required_columns = {'email', 'voter_code'}
            if not required_columns.issubset(set(reader.fieldnames)):
                raise ValidationError(
                    f'CSV must contain columns: {", ".join(required_columns)}. '
                    f'Optional: full_name'
                )
            
            # Validate at least one row
            rows = list(reader)
            if not rows:
                raise ValidationError('CSV file must contain at least one voter.')
            
        except UnicodeDecodeError:
            raise ValidationError('CSV file must be UTF-8 encoded.')
        except Exception as e:
            raise ValidationError(f'Error reading CSV file: {str(e)}')
        
        return csv_file
    
    def save(self, commit=True):
        """Save voter list and import voters from CSV"""
        voter_list = super().save(commit=commit)
        
        if commit:
            # Import voters from CSV
            self._import_voters_from_csv(voter_list)
        
        return voter_list
    
    def _import_voters_from_csv(self, voter_list):
        """Import voters from uploaded CSV file"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file:
            return
        
        try:
            content = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            voters_to_create = []
            voter_codes_seen = set()
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                email = row.get('email', '').strip()
                voter_code = row.get('voter_code', '').strip()
                full_name = row.get('full_name', '').strip()
                
                # Validate required fields
                if not email or not voter_code:
                    continue
                
                # Prevent duplicates within the CSV
                if voter_code in voter_codes_seen:
                    continue
                
                voter_codes_seen.add(voter_code)
                
                # Collect additional fields
                additional_info = {}
                for key, value in row.items():
                    if key not in ['email', 'voter_code', 'full_name']:
                        additional_info[key] = value
                
                # Create voter object
                voter = Voter(
                    voter_list=voter_list,
                    email=email,
                    voter_code=voter_code,
                    full_name=full_name,
                    additional_info=additional_info
                )
                
                voters_to_create.append(voter)
            
            # Bulk create voters
            if voters_to_create:
                # Use ignore_conflicts to skip duplicate voter codes
                Voter.objects.bulk_create(
                    voters_to_create,
                    ignore_conflicts=True
                )
                
                # Update total_voters count
                voter_list.total_voters = Voter.objects.filter(voter_list=voter_list).count()
                voter_list.save(update_fields=['total_voters'])
        
        except Exception as e:
            # Log the error but don't fail
            print(f"Error importing voters: {str(e)}")


class CampaignVotingModeForm(forms.ModelForm):
    """Form for configuring voting mode for campaigns"""
    
    class Meta:
        model = VotingCampaign
        fields = [
            'voting_mode',
            'voter_list',
            'device_tracking_method',
            'enable_ip_restriction'
        ]
        widgets = {
            'voting_mode': forms.RadioSelect(choices=VotingCampaign.VOTING_MODE_CHOICES, attrs={
                'class': 'form-check-input'
            }),
            'voter_list': forms.Select(attrs={
                'class': 'form-control'
            }),
            'device_tracking_method': forms.Select(
                choices=VotingCampaign.DEVICE_TRACKING_CHOICES,
                attrs={'class': 'form-control'}
            ),
            'enable_ip_restriction': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        voting_mode = cleaned_data.get('voting_mode')
        voter_list = cleaned_data.get('voter_list')
        
        if voting_mode == 'authenticated' and not voter_list:
            raise ValidationError(
                'A voter list is required for authenticated voting mode.'
            )
        
        return cleaned_data
