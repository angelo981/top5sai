# Candidate Activities & Achievements Feature Documentation

## Overview
The Candidate Activities & Achievements feature allows candidates to showcase their work, projects, and accomplishments to voters in a visually compelling way. This feature includes:

1. **Activity Photo Gallery** - An interactive carousel/slider for showcasing multiple photos
2. **Achievements Section** - Display key accomplishments with icons and descriptions
3. **Media & Video Embeds** - Support for YouTube, TikTok, and direct video uploads

## Database Models

### 1. CandidateAchievement
Stores key accomplishments and achievements for each candidate.

**Fields:**
- `candidate` (ForeignKey) - Reference to the Candidate
- `title` (CharField) - Title of the achievement (max 255 chars)
- `description` (TextField) - Detailed description of the achievement
- `icon` (CharField) - FontAwesome icon class (default: 'fa-star')
  - Examples: `fa-trophy`, `fa-medal`, `fa-award`, `fa-star`
- `order` (PositiveIntegerField) - Display order (default: 0)
- `created_at` (DateTimeField) - Auto-timestamp

**Display:** Grid layout with 200px minimum width cards, showing icon, title, and description

### 2. CandidateActivityPhoto
Stores activity photos in a gallery with metadata for the carousel.

**Fields:**
- `candidate` (ForeignKey) - Reference to the Candidate
- `photo` (ImageField) - Photo file uploaded to `voting/candidates/activities/`
- `caption` (CharField) - Photo caption/title (max 300 chars, optional)
- `description` (TextField) - Detailed description of the activity (optional)
- `activity_type` (CharField) - Type of activity with choices:
  - `event` - Community Event
  - `project` - Project/Work
  - `achievement` - Achievement
  - `initiative` - Initiative
  - `other` - Other
- `order` (PositiveIntegerField) - Display order in gallery (default: 0)
- `created_at` (DateTimeField) - Auto-timestamp

**Display:** Interactive carousel with 250px height, navigation buttons, indicators, and captions

### 3. CandidateMedia
Stores video links and embeddings for rich media presentation.

**Fields:**
- `candidate` (ForeignKey) - Reference to the Candidate
- `media_type` (CharField) - Type of media with choices:
  - `youtube` - YouTube Video
  - `tiktok` - TikTok Video
  - `video_file` - Video File Upload
  - `other` - Other Video Link
- `title` (CharField) - Title of the video/media (max 255 chars)
- `description` (TextField) - Description of the video/media (optional)
- `embed_url` (URLField) - URL to the video (YouTube link, TikTok link, etc.) (optional)
- `video_file` (FileField) - Video file upload to `voting/candidates/videos/` (optional)
- `youtube_video_id` (CharField) - Auto-extracted YouTube video ID (max 100 chars)
- `tiktok_video_id` (CharField) - Auto-extracted TikTok video ID (max 100 chars)
- `order` (PositiveIntegerField) - Display order (default: 0)
- `created_at` (DateTimeField) - Auto-timestamp

**Features:**
- Auto-extracts YouTube video IDs from URLs
- Auto-extracts TikTok video IDs from URLs
- Supports direct video uploads or embedded links
- Platform-specific badges and icons

**Display:** Grid layout with 280px minimum width cards, showing media thumbnail, title, description, and watch/download link

## Admin Interface

### Managing Activities in Django Admin

1. **Candidate Admin Page:**
   - Click on a Candidate in the voting app admin
   - Three inline admin sections are available:
     - **Candidate Achievements** - Add/edit/delete achievements
     - **Candidate Activity Photos** - Add/edit/delete activity photos
     - **Candidate Media** - Add/edit/delete video links

2. **Separate Admin Pages:**
   - Each model has its own admin registration
   - Can be managed independently
   - Organized by campaign and candidate

### How to Add Activities

#### Adding Achievements:
1. In Candidate admin, scroll to "Candidate Achievements" section
2. Click "Add another Candidate Achievement"
3. Fill in:
   - Title (e.g., "Community Service Award")
   - Description (e.g., "Awarded for outstanding community service")
   - Icon (FontAwesome class, e.g., "fa-trophy")
   - Order (numeric value for display order)
4. Click Save

#### Adding Activity Photos:
1. In Candidate admin, scroll to "Candidate Activity Photos" section
2. Click "Add another Candidate Activity Photo"
3. Fill in:
   - Photo (upload image file)
   - Caption (short title, e.g., "Environmental Cleanup Event")
   - Description (optional detailed description)
   - Activity Type (select from Event, Project, Achievement, Initiative, Other)
   - Order (numeric value for display order)
4. Click Save

#### Adding Videos:
1. In Candidate admin, scroll to "Candidate Media" section
2. Click "Add another Candidate Media"
3. Fill in:
   - Media Type (YouTube, TikTok, Video File, or Other)
   - Title (e.g., "Campaign Speech")
   - Description (optional)
   - For YouTube: Embed URL (e.g., https://www.youtube.com/watch?v=xxx)
   - For TikTok: Embed URL (e.g., https://www.tiktok.com/@user/video/xxx)
   - For Video File: Upload video file
   - Order (numeric value for display order)
4. Click Save

## Frontend Display

### On Campaign Detail Page

The activities section appears on each candidate card and includes:

1. **Expand Button:** "View Activities" button appears if candidate has any activities/achievements/media
2. **Collapsible Section:** Clicking the button expands a detailed activities panel showing:

   - **Activity Gallery:** 
     - Interactive carousel with left/right navigation buttons
     - Carousel indicators (dots) at the bottom
     - Image display with 75% height
     - Caption section showing activity title and type
     - Keyboard navigation support (arrow keys)

   - **Achievements Section:**
     - Grid layout of achievement badges
     - Each badge shows: icon, title, and description
     - Hover effects with elevation
     - Responsive grid (auto-fill, minmax 200px)

   - **Media Section:**
     - Grid of media items (YouTube, TikTok, or video files)
     - Platform-specific icons and badges
     - Thumbnail with play icon
     - "Watch" or "Download" link
     - Responsive grid layout

### Design Features

- **Color Scheme:** Matches TOP5SAI primary blue (#667eea) and gradients
- **Responsive Design:** Works on mobile, tablet, and desktop
- **Animation:** Smooth transitions and slide-down animations
- **Accessibility:** Keyboard navigation support, semantic HTML

### CSS Classes Reference

**Container Classes:**
- `.candidate-activities-section` - Main container
- `.activity-gallery-container` - Gallery wrapper
- `.achievements-container` - Achievements wrapper
- `.media-container` - Media wrapper

**Gallery Classes:**
- `.activity-carousel` - Carousel container
- `.carousel-slides` - Slides wrapper
- `.carousel-slide` - Individual slide
- `.carousel-nav` - Navigation buttons
- `.carousel-indicators` - Indicator dots

**Achievement Classes:**
- `.achievements-list` - Grid container
- `.achievement-badge` - Individual achievement card
- `.achievement-icon` - Icon element
- `.achievement-title` - Title element
- `.achievement-description` - Description element

**Media Classes:**
- `.media-grid` - Grid container
- `.media-item` - Individual media card
- `.media-thumbnail` - Thumbnail area
- `.media-info` - Information area
- `.media-type-badge` - Type badge (youtube, tiktok, video)

## JavaScript Functions

### Activity Section Toggle
```javascript
toggleActivities(event, candidateId)
```
- Toggles visibility of activities section
- Updates button text and icon

### Carousel Navigation
```javascript
nextSlide(candidateId)           // Go to next slide
prevSlide(candidateId)           // Go to previous slide
goToSlide(candidateId, slideIndex) // Go to specific slide
updateCarousel(candidateId)      // Internal: updates carousel display
```

### Features:
- Seamless looping (first slide loops to last, etc.)
- Indicator dots highlight current slide
- Keyboard arrow navigation support
- Smooth CSS transitions

## Migration Information

**Migration File:** `voting/migrations/0006_candidateachievement_candidateactivityphoto_and_more.py`

**Tables Created:**
- `voting_candidateachievement`
- `voting_candidateactivityphoto`
- `voting_candidatemedia`

## File Uploads

### Directory Structure
```
media/
├── voting/
│   └── candidates/
│       ├── activities/      # Activity photos
│       ├── videos/          # Video uploads
│       └── [existing files]
```

### Supported Formats

**Images:**
- JPG, JPEG, PNG, AVIF, WebP
- Max size: Depends on Django settings (default: unlimited)
- Recommended: High-quality images for gallery display

**Videos:**
- MP4, WebM, MOV
- For direct uploads only (not YouTube/TikTok links)
- Recommended: Compressed format for web

## Performance Considerations

1. **Image Optimization:** Consider compressing images before upload
2. **Lazy Loading:** Images load as carousel slides are viewed
3. **Database Queries:** Use Django admin's `select_related` for efficient queries
4. **Carousel Efficiency:** Only active carousel in viewport processes interactions

## Responsive Breakpoints

- **Desktop (>768px):** Full-size grid layouts, 250px carousel height
- **Tablet (481-768px):** Adjusted grid columns, 200px carousel height
- **Mobile (<480px):** Single/dual column grids, 200px carousel height

## Browser Compatibility

- Chrome/Chromium: Full support
- Firefox: Full support
- Safari: Full support
- Edge: Full support
- IE 11: Limited support (basic gallery, no animations)

## Future Enhancements

1. **Drag-and-Drop Reordering:** Reorder achievements and photos in admin
2. **Batch Upload:** Upload multiple photos at once
3. **Social Media Integration:** Auto-fetch Instagram posts/TikTok videos
4. **Image Cropping:** Built-in image editor in admin
5. **Advanced Analytics:** Track views per activity/achievement
6. **Voting Impact:** Show how each activity influences votes

## Troubleshooting

### Activities Not Showing
- Check if candidate has any achievements/photos/media
- Verify migrations are applied: `python manage.py migrate`
- Check Django admin to ensure data is created

### Images Not Displaying
- Verify media files are in correct directory
- Check Django `MEDIA_URL` and `MEDIA_ROOT` settings
- Ensure web server is serving media files

### Carousel Not Working
- Check browser console for JavaScript errors
- Verify candidate ID is correctly passed
- Check if CSS is properly loaded

### Videos Not Embedding
- For YouTube: Verify URL is correct format
- For TikTok: Ensure public video link
- Check if embed_url field is properly populated

## Support & Maintenance

For issues or feature requests:
1. Check Django error logs
2. Verify database migrations are applied
3. Clear browser cache and reload
4. Check Django admin for data integrity
