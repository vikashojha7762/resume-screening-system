# Interview Toggle UI Implementation

## Overview

The interview toggle functionality has been implemented in the frontend UI. Users can now shortlist candidates and enable/disable interviews directly from the Candidates table.

## Features Implemented

### 1. Interview Toggle in Candidates Table

**Location:** `frontend/src/pages/Candidates.tsx`

**Features:**
- **Shortlist Toggle**: Switch to shortlist/unshortlist candidates
- **Interview Toggle**: Enable/disable interview scheduling (only visible when candidate is shortlisted)
- **Visual Indicators**: 
  - Checkmark icon when shortlisted
  - Calendar icon when interview is enabled
  - Color-coded switches
- **Loading States**: Disabled switches while API calls are in progress

### 2. Redux State Management

**Location:** `frontend/src/store/slices/interviewsSlice.ts`

**Actions:**
- `shortlistCandidate` - Shortlist or unshortlist a candidate
- `toggleInterviewEnabled` - Enable/disable interview scheduling
- `fetchInterviewStatus` - Get current interview status for a candidate
- `fetchInterviews` - Get list of scheduled interviews
- `scheduleInterview` - Schedule a new interview

### 3. API Service

**Location:** `frontend/src/services/interviewService.ts`

**Functions:**
- `shortlistCandidate()` - POST `/candidates/{id}/shortlist`
- `toggleInterview()` - POST `/candidates/{id}/toggle-interview`
- `getInterviewStatus()` - GET `/candidates/{id}/interview-status`
- `scheduleInterview()` - POST `/interviews`
- `getInterviews()` - GET `/interviews`
- `updateInterview()` - PUT `/interviews/{id}`
- `cancelInterview()` - POST `/interviews/{id}/cancel`

## UI Components

### Candidates Table Columns

1. **Rank** - Candidate ranking
2. **Candidate ID** - Name and resume file
3. **Score** - Overall match score
4. **Skills** - Skills match percentage
5. **Experience** - Experience match percentage
6. **Education** - Education match percentage
7. **Shortlisted** - Toggle switch with checkmark icon
8. **Interview** - Toggle switch with calendar icon (only when shortlisted)
9. **Actions** - View details button

### Visual States

- **Not Shortlisted**: 
  - Switch OFF
  - Cancel icon (gray)
  - Interview toggle shows "Shortlist first" message

- **Shortlisted**:
  - Switch ON
  - Checkmark icon (green)
  - Interview toggle becomes active

- **Interview Enabled**:
  - Switch ON
  - Calendar icon (blue if online, gray if offline)

- **Updating**:
  - Switch disabled
  - Loading state

## Usage Flow

1. **Match Candidates**: Click "Match Candidates" button
2. **Shortlist**: Toggle the shortlist switch for desired candidates
3. **Enable Interview**: Toggle the interview switch (only available for shortlisted candidates)
4. **View Details**: Click the eye icon to see candidate details

## API Integration

### Shortlist Candidate
```typescript
POST /api/v1/candidates/{candidate_id}/shortlist?job_id={job_id}&shortlisted=true
```

### Toggle Interview
```typescript
POST /api/v1/candidates/{candidate_id}/toggle-interview?job_id={job_id}
Body: {
  "interview_enabled": true,
  "online_interview_enabled": false
}
```

### Get Interview Status
```typescript
GET /api/v1/candidates/{candidate_id}/interview-status?job_id={job_id}
```

## State Management

The interview state is stored in Redux:
- `interviews.interviewStatuses` - Map of candidate-job statuses
- `interviews.interviews` - List of scheduled interviews
- `interviews.updatingCandidates` - Array of candidate IDs being updated
- `interviews.isLoading` - Loading state
- `interviews.error` - Error messages

## Error Handling

- API errors are caught and displayed
- Failed operations show error messages
- Switches are disabled during API calls to prevent duplicate requests
- Network errors are handled gracefully

## Next Steps (Future Enhancements)

1. **Interview Scheduling Form**: Add modal/form to schedule interviews
2. **Interview Calendar**: Show scheduled interviews in calendar view
3. **Interview Details Page**: View and manage interview details
4. **Online Interview Link**: Display and copy meeting links
5. **Interview Status Badges**: Show scheduled, completed, cancelled statuses
6. **Bulk Actions**: Shortlist multiple candidates at once

## Files Modified/Created

### Created:
- `frontend/src/services/interviewService.ts` - API service functions
- `frontend/src/store/slices/interviewsSlice.ts` - Redux slice

### Modified:
- `frontend/src/pages/Candidates.tsx` - Added interview toggle UI
- `frontend/src/store/index.ts` - Added interviews reducer
- `frontend/src/types/index.ts` - Added interview fields to MatchResult

## Testing

To test the implementation:

1. Start the backend server
2. Start the frontend dev server
3. Navigate to Candidates page
4. Select a job and click "Match Candidates"
5. Toggle shortlist switch for a candidate
6. Toggle interview switch (should be enabled after shortlisting)
7. Check browser console for any errors
8. Verify API calls in Network tab

## Notes

- Interview toggle is only visible when candidate is shortlisted
- All API calls require authentication (JWT token)
- State is automatically synced after successful API calls
- Interview status is fetched automatically after matching candidates

