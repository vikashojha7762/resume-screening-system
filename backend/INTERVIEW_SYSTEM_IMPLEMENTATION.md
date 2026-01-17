# Interview Scheduling System Implementation

## Overview

This document describes the interview scheduling and online interview system added to the Intelligent Resume Screening System. All changes are **additive and backward-compatible**.

## Architecture

### Database Changes

#### New Tables

1. **`interviews`** - Stores interview scheduling information
   - Links job, candidate, and scheduler
   - Tracks interview date, time, duration, type (ONLINE/OFFLINE)
   - Stores meeting links and room IDs for online interviews
   - Tracks attendance (candidate_joined_at, interviewer_joined_at)
   - Status: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW

2. **`interview_logs`** - Audit trail for all interview actions
   - Logs: SCHEDULED, RESCHEDULED, CANCELLED, JOINED, COMPLETED, etc.
   - Tracks old/new values for changes
   - Includes action reason and user who performed action

#### Modified Tables

1. **`match_results`** - Added fields (backward-compatible):
   - `shortlisted` (Boolean, default: false) - Whether candidate is shortlisted
   - `interview_enabled` (Boolean, default: false) - Toggle to enable interview scheduling
   - `online_interview_enabled` (Boolean, default: false) - Toggle for online interview

### Models

#### `app/models/interview.py`
- `Interview` - Main interview model
- `InterviewType` - Enum: ONLINE, OFFLINE
- `InterviewStatus` - Enum: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW
- `InterviewLog` - Audit log model

#### `app/models/match_result.py`
- Added: `shortlisted`, `interview_enabled`, `online_interview_enabled` fields

### Services

#### `app/services/interview_scheduler.py`
- `InterviewScheduler` - Manages interview scheduling, updates, cancellation
- Validates:
  - Candidate must be shortlisted
  - Interview must be enabled
  - Interview date must be in future
  - Minimum 2 hours advance notice
  - Maximum 90 days in advance
  - No conflicting interviews
- Auto-updates status:
  - SCHEDULED → COMPLETED (after duration ends)
  - SCHEDULED → NO_SHOW (if candidate doesn't join)

#### `app/services/online_interview_service.py`
- `OnlineInterviewService` - Manages online interview links
- Generates secure, unguessable meeting room IDs
- Validates meeting access:
  - Room ID must match
  - Interview must be SCHEDULED or IN_PROGRESS
  - Online interview must be enabled
  - Current time must be within allowed window (15 min before to 15 min after)
- Provider abstraction: INTERNAL_VIDEO_ROOM (extensible to ZOOM, GOOGLE_MEET)

### API Endpoints

#### Interview Management (`/api/v1/interviews`)

1. **POST `/interviews`** - Schedule interview
   - Requires: candidate shortlisted, interview enabled
   - Validates: future date, advance notice, no conflicts
   - Generates meeting link if online enabled

2. **GET `/interviews`** - List interviews
   - Supports pagination
   - Filters: job_id, candidate_id, status

3. **GET `/interviews/{interview_id}`** - Get interview details

4. **PUT `/interviews/{interview_id}`** - Update/reschedule interview
   - Logs changes in audit trail

5. **POST `/interviews/{interview_id}/cancel`** - Cancel interview
   - Requires cancellation reason

6. **POST `/interviews/{interview_id}/join`** - Join online interview
   - Validates access (room ID, status, time window)
   - Marks attendance
   - No authentication required (candidates don't have accounts)

7. **GET `/interviews/{interview_id}/logs`** - Get audit logs

8. **POST `/interviews/auto-update-status`** - Auto-update statuses
   - Can be called by cron job

#### Candidate Management (`/api/v1/candidates`)

1. **POST `/candidates/{candidate_id}/shortlist`** - Shortlist/unshortlist candidate
   - Sets `shortlisted` flag
   - Disables interview if unshortlisting

2. **POST `/candidates/{candidate_id}/toggle-interview`** - Toggle interview enabled
   - Requires: candidate must be shortlisted
   - If interview disabled, online is also disabled

3. **GET `/candidates/{candidate_id}/interview-status`** - Get interview status

### Workflow

```
1. Match Candidates → Generate Match Results
2. Shortlist Candidate → Set shortlisted = true
3. Enable Interview → Set interview_enabled = true
4. Schedule Interview → Create Interview record
   - If online_interview_enabled: Generate meeting link
5. Candidate/Interviewer Join → Mark attendance, update status to IN_PROGRESS
6. Auto-Update Status → COMPLETED or NO_SHOW after duration
```

### Security

- Meeting room IDs are secure and unguessable (SHA-256 hash)
- Access validation:
  - Room ID must match
  - Interview must be in valid status
  - Time window enforcement (15 min buffer)
- Interview links expire after 24 hours
- Audit logging for all actions

### Migration

Run the Alembic migration:
```bash
alembic upgrade head
```

Migration file: `backend/alembic/versions/003_add_interview_system.py`

### Frontend Integration (TODO)

The following UI components need to be created:

1. **Candidate Table**
   - Shortlist toggle
   - Interview enabled toggle (only if shortlisted)
   - Interview status badge

2. **Candidate Detail Page**
   - Interview schedule form
   - Online interview toggle
   - Interview timeline
   - Join Interview button (for candidates)

3. **Dashboard**
   - Upcoming Interviews widget
   - Interviews Today widget
   - Completed Interviews widget

### Testing Checklist

- [ ] Shortlist candidate
- [ ] Enable interview for shortlisted candidate
- [ ] Schedule interview (future date)
- [ ] Validate: cannot schedule if not shortlisted
- [ ] Validate: cannot schedule if interview not enabled
- [ ] Validate: cannot schedule in past
- [ ] Reschedule interview
- [ ] Cancel interview
- [ ] Generate online meeting link
- [ ] Join interview (candidate)
- [ ] Join interview (interviewer)
- [ ] Validate: cannot join outside time window
- [ ] Auto-update status to COMPLETED
- [ ] Auto-update status to NO_SHOW
- [ ] View interview logs

### Notes

- All changes are **additive** - no existing functionality is broken
- Default values ensure backward compatibility
- Interview features only activate after shortlisting
- Online interview requires interview to be enabled first
- Meeting links are generated on-demand when online interview is enabled

