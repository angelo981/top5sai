# Voting System Setup Guide - TOP5SAI

## Overview
A complete voting system has been created for TOP5SAI, allowing administrators to create voting campaigns and manage voting categories and candidates. The system includes:

- **Admin Dashboard**: Manage campaigns, categories, candidates, and view voting results
- **Public Voting Interface**: Attractive voting pages for users to cast their votes
- **Live Results**: Real-time vote counting and results display
- **Security**: IP-based duplicate vote prevention
- **Responsive Design**: Fully responsive for desktop and mobile devices

## Setup Instructions

### 1. Create Database Migrations
Run the following command to create the necessary database tables:

```bash
python manage.py makemigrations voting
python manage.py migrate voting
```

### 2. Create a Superuser (if not already created)
Create an admin account to access the admin dashboard:

```bash
python manage.py createsuperuser
```

### 3. Start the Development Server
```bash
python manage.py runserver
```

### 4. Access the Admin Dashboard
Navigate to: `http://127.0.0.1:8000/admin/`

## Creating Your First Voting Campaign

### Step 1: Create a Campaign
1. Go to the Django Admin Dashboard
2. Navigate to "Voting Campaigns"
3. Click "Add Voting Campaign"
4. Fill in the following fields:
   - **Title**: Campaign name (e.g., "Best Artist 2024")
   - **Description**: Detailed campaign description
   - **Short Description**: Brief summary for campaign cards (max 300 characters)
   - **Banner**: Upload a campaign banner image
   - **Status**: Set to "Active" for the campaign to be visible
   - **Start Date**: When voting begins
   - **End Date**: When voting ends

### Step 2: Create Categories
1. In the campaign edit page, scroll down to "Voting Categories"
2. Click "Add another Voting Category"
3. Fill in:
   - **Name**: Category name (e.g., "Best Male Artist")
   - **Description**: Optional category description
   - **Order**: Display order (lower numbers appear first)

### Step 3: Add Candidates
1. Go to "Candidates" in the admin menu
2. Click "Add Candidate"
3. Fill in:
   - **Category**: Select the category this candidate belongs to
   - **Name**: Candidate name
   - **Description**: Optional description
   - **Photo**: Upload candidate photo
   - **Order**: Display order

## Features

### For Administrators
- Create and manage voting campaigns
- Organize candidates into categories
- View live voting statistics and trends
- Track voting activity and IP addresses
- Download voting reports

### For Users
- Browse active voting campaigns with attractive cards
- View campaign details and timeline
- Vote in multiple categories
- See live vote counts and percentages
- Track voting progress with animated bars

## URL Structure

- **Campaign List**: `/voting/` (linked from navbar "VOTE NOW" button)
- **Campaign Details**: `/voting/campaign/<id>/`
- **Submit Vote**: `/voting/campaign/<id>/category/<category_id>/vote/` (POST)
- **Get Results**: `/voting/campaign/<id>/category/<category_id>/results/` (GET)

## Models

### VotingCampaign
- Stores campaign information
- Status options: Draft, Active, Closed, Archived
- Tracks total votes and days remaining

### VotingCategory
- Groups candidates within a campaign
- Supports custom ordering

### Candidate
- Individual voting options
- Includes photo and description
- Tracks vote count and percentage automatically

### Vote
- Records each vote with:
  - Voter IP address (for duplicate prevention)
  - Timestamp
  - Campaign, Category, and Candidate references

## Security Features

1. **Duplicate Vote Prevention**: IP-based tracking prevents the same voter from voting twice in the same category
2. **CSRF Protection**: Django's CSRF middleware protects against cross-site attacks
3. **Data Validation**: Server-side validation of all vote submissions
4. **Admin Restrictions**: Vote records are read-only; admins cannot manually add votes

## Customization

### Styling
The voting templates use Bootstrap classes and custom CSS. To customize:
- Campaign list styling: Edit `voting/templates/voting/campaign_list.html`
- Voting interface styling: Edit `voting/templates/voting/campaign_detail.html`

### Colors
The current color scheme uses #ce9233 (gold) as the primary color. To change:
1. Edit the hex color in the CSS blocks within the templates
2. Or update your main CSS file (css/style.css)

### Image Uploads
- Campaign banners are stored in: `media/voting/campaigns/banners/`
- Candidate photos are stored in: `media/voting/candidates/`

## Sample Data Creation

To create sample data for testing, run the following Django shell commands:

```python
python manage.py shell

from django.utils import timezone
from datetime import timedelta
from voting.models import VotingCampaign, VotingCategory, Candidate

# Create a campaign
campaign = VotingCampaign.objects.create(
    title="Best Artist 2024",
    description="Vote for your favorite artist of 2024",
    short_description="Participate in our annual artist voting",
    status='active',
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=30)
)

# Create a category
category = VotingCategory.objects.create(
    campaign=campaign,
    name="Best Male Artist",
    order=1
)

# Create candidates
Candidate.objects.create(
    category=category,
    name="Artist 1",
    description="Talented artist from Rwanda",
    order=1
)

Candidate.objects.create(
    category=category,
    name="Artist 2",
    description="Popular international artist",
    order=2
)

print("Sample data created successfully!")
```

## Testing

Run the included tests with:

```bash
python manage.py test voting
```

## Troubleshooting

### Campaign not showing on voting page
- Check that the campaign status is set to "Active"
- Verify that the start date has passed and end date is in the future

### Vote submission fails
- Check that the candidate belongs to the correct category
- Verify CSRF token is present in the page
- Check browser console for JavaScript errors

### Images not displaying
- Ensure Django DEBUG = True (for development)
- Check that media files are properly uploaded
- Verify MEDIA_URL and MEDIA_ROOT settings in settings.py

## Admin Customization

The voting app includes a fully configured Django admin interface. To further customize:

Edit `voting/admin.py` to:
- Add more filters
- Customize list display columns
- Add search fields
- Change field organization in forms

## Next Steps

1. Create your first voting campaign through the admin dashboard
2. Add categories and candidates
3. Share the voting link with users
4. Monitor voting activity through the admin dashboard

## Support

For issues or questions:
1. Check the Django logs for error messages
2. Review the voting models and views for the data structure
3. Verify all migrations have been applied: `python manage.py showmigrations`
