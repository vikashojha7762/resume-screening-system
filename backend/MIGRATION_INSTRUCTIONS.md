# Database Migration Instructions

## Problem
The `match_results` table is missing the following columns:
- `interview_enabled` (BOOLEAN)
- `online_interview_enabled` (BOOLEAN)  
- `shortlisted` (BOOLEAN)

This causes the shortlist toggle to fail with: `column match_results.interview_enabled does not exist`

## Solution

### Option 1: Run Alembic Migration (Recommended)

```bash
cd backend
alembic upgrade head
```

This will apply all pending migrations, including:
- Migration 003: Adds interview system (includes match_results columns)
- Migration 004: Safe migration that checks and adds columns if missing

### Option 2: Manual SQL (If Migration Fails)

If Alembic migration fails, you can manually add the columns:

```sql
-- Connect to your PostgreSQL database
-- Then run:

ALTER TABLE match_results 
ADD COLUMN IF NOT EXISTS interview_enabled BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE match_results 
ADD COLUMN IF NOT EXISTS online_interview_enabled BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE match_results 
ADD COLUMN IF NOT EXISTS shortlisted BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS ix_match_results_shortlisted ON match_results(shortlisted);
```

### Option 3: Check Current Migration Status

```bash
cd backend
alembic current
```

This shows which migration is currently applied.

### Verify Migration Success

After running the migration, verify the columns exist:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'match_results' 
AND column_name IN ('interview_enabled', 'online_interview_enabled', 'shortlisted');
```

You should see all three columns listed.

## Troubleshooting

### If migration 003 fails:
- Migration 004 is designed to be safe - it checks if columns exist before adding them
- You can run migration 004 directly if 003 has issues

### If you get "revision not found" error:
- Check which migrations exist: `ls alembic/versions/`
- Check current revision: `alembic current`
- You may need to manually set the revision: `alembic stamp <revision_id>`

### If columns still don't exist after migration:
- Check database connection
- Verify you're connected to the correct database
- Run the manual SQL commands (Option 2)

