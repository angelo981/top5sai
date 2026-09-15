# Voting System - User Guide

## For Voters

### How to Vote

1. **Navigate to Voting Campaign**
   - Go to the voting page
   - Select an active campaign
   
2. **View Candidates**
   - Scroll through categories (displayed in rows)
   - Each category shows all candidates with:
     - Candidate photo
     - Candidate name
     - Candidate description
     - Current vote count and percentage (if live results enabled)

3. **Cast Your Vote**
   - Select a candidate by clicking the radio button on their card
   - The selected candidate card highlights in gold
   - Click the **"Cast Your Vote"** button
   - You'll see a success message confirming your vote

4. **Vote Restrictions**
   - You can only vote once per category
   - The system prevents duplicate votes from the same IP address
   - If you try to vote again, you'll see an error message

5. **View Results**
   - Click **"View Results"** button in the campaign header
   - Results page shows ranked candidates with:
     - Ranking badges (gold for 1st, silver for 2nd, bronze for 3rd)
     - Vote counts and percentages
     - Progress bars showing vote distribution
     - Results update automatically every 5 seconds

## For Administrators

### Configure Voting Campaign

1. **Access Django Admin**
   - Go to Admin panel
   - Navigate to "Voting Campaigns"

2. **Create/Edit Campaign**
   - Fill in basic information (title, description, banner)
   - Set campaign status (Draft, Active, Closed, Archived)
   - Set start and end dates

3. **Configure Results Settings**

   **Results Visibility**:
   - `Hidden` - Results not visible to anyone
   - `During Voting` - Visible while campaign is active
   - `After Voting` - Visible only after end date (recommended)
   - `Always` - Results always visible

   **Results Access Control**:
   - `Everyone` - All users can view results
   - `Authenticated Users Only` - Must be logged in
   - `Administrators Only` - Staff members only

   **Live Results Display**:
   - Toggle `Show Live Results` to control vote count visibility during voting
   - When enabled, voters see live vote counts and percentages
   - Results auto-update every 5 seconds

4. **Add Categories and Candidates**
   - Use inline editors to add categories
   - For each category, add candidates with:
     - Name
     - Description
     - Photo
     - Display order

### Monitor Campaign

1. **View Voting Progress**
   - Admin panel shows total votes per campaign
   - Candidate list shows vote count and percentage

2. **Access Results**
   - Visit the results page to see rankings
   - Results respect visibility settings

3. **Manage Access**
   - Adjust visibility settings anytime
   - Results immediately reflect new settings

## Results Page Features

### What Voters See

**Available (when permitted)**:
- Ranked candidates by vote count
- Vote counts and percentages
- Visual progress bars
- Candidate photos and descriptions
- Real-time updates

**Unavailable (based on settings)**:
- "Results are not currently available" message
- Explanation of when results will be visible
- Link to return to voting page

### Ranking Display

- **1st Place**: Gold badge with trophy
- **2nd Place**: Silver badge
- **3rd Place**: Bronze badge
- **Other**: Gray badge with number
- Progress bars show relative vote distribution

## Voting Rules

### Duplicate Vote Prevention

- **One vote per IP address per category**
- **Enforced at database level** (unique constraint)
- **Error handling** shows message if attempting duplicate vote

### Voting Window

- Can only vote while campaign is "Active"
- Voting restricted before start date
- Voting restricted after end date
- Status displays campaign state

## Example Scenarios

### Scenario 1: During Voting with Live Results
```
✅ Admin enables live results
✅ Voters see vote counts updating
✅ Results page shows current rankings
✅ Auto-refreshes every 5 seconds
```

### Scenario 2: After Voting Ends
```
✅ Campaign status changes to "Closed"
✅ Voting buttons become disabled
✅ Results become visible (if configured for "After Voting")
✅ Rankings show final vote counts
```

### Scenario 3: Admin-Only Results
```
✅ Admin sets access to "Administrators Only"
✅ Regular users see "access denied" message
✅ Only staff can view results
```

## Tips & Best Practices

1. **Set Results to "After Voting"**
   - Encourages voting participation
   - Prevents voting bias from seeing results

2. **Enable Live Results for Engagement**
   - Shows activity during voting
   - Increases voter participation

3. **Test Before Going Live**
   - Create a draft campaign
   - Test voting and results visibility
   - Verify settings work as expected

4. **Monitor Vote Distribution**
   - Use admin panel to track progress
   - Watch for unusual voting patterns

5. **Communicate Results Settings**
   - Inform voters when results will be visible
   - Set clear voting timeline
   - Announce results visibility schedule

## Troubleshooting

### "You have already voted in this category"
- You've already cast a vote from this IP address
- Results are binding and cannot be changed
- Each category allows only one vote per IP

### Results Page Shows "Not Available"
- Results visibility setting not met
- Voting period may still be ongoing
- You may lack permission to view results
- Check with admin about visibility settings

### Live Results Not Updating
- Admin may have disabled "Show Live Results"
- Refresh the page manually
- Try returning to voting page and back to results

### Can't Vote
- Campaign may not be active
- You may have already voted in this category
- Voting period may have ended
- Check campaign dates and status

---

**Questions?** Contact your administrator for help with the voting system.
