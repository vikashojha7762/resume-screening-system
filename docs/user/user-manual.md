# User Manual

Complete guide to using the Resume Screening System.

## Table of Contents

- [Dashboard](#dashboard)
- [Job Management](#job-management)
- [Resume Management](#resume-management)
- [Candidate Matching](#candidate-matching)
- [Reports and Analytics](#reports-and-analytics)
- [Settings](#settings)

## Dashboard

### Overview

The dashboard provides a high-level view of your hiring pipeline:

- **Active Jobs** - Currently open positions
- **Total Resumes** - All resumes in system
- **Candidates Matched** - Total matches made
- **Average Match Score** - Overall quality metric

### Quick Actions

- **Create New Job** - Quick access to job creation
- **Upload Resumes** - Direct upload button
- **View Recent Matches** - Latest matching results

## Job Management

### Creating Jobs

1. Navigate to **Jobs** → **Create Job**
2. Fill required fields:
   - **Title** (required)
   - **Description** (required)
   - **Requirements** (optional but recommended)

3. Configure requirements:
   ```json
   {
     "required_skills": ["Python", "FastAPI"],
     "preferred_skills": ["Docker"],
     "min_experience_years": 3,
     "required_degree": "Bachelor's"
   }
   ```

4. Set status:
   - **Draft** - Not yet active
   - **Active** - Accepting applications
   - **Closed** - No longer accepting
   - **Archived** - Historical record

### Managing Jobs

- **Edit** - Update job details
- **Duplicate** - Create similar job quickly
- **Close** - Stop accepting applications
- **Delete** - Remove job (with confirmation)

### Job Statuses

- **Draft:** Work in progress
- **Active:** Live and accepting resumes
- **Closed:** Position filled or cancelled
- **Archived:** Historical record

## Resume Management

### Upload Methods

#### Drag and Drop
1. Drag files onto the upload area
2. Drop to start upload
3. Multiple files supported

#### File Selection
1. Click upload area
2. Select files from dialog
3. Click "Open"

#### Bulk Upload
1. Select multiple files (Ctrl/Cmd + Click)
2. Upload all at once
3. Track progress for each file

### Resume Status

Monitor processing status:

- **Uploaded** ⏳ - File received, queued
- **Parsing** 🔄 - Extracting text
- **Parsed** ✅ - Text extracted
- **Processing** 🔄 - Running analysis
- **Processed** ✅ - Ready for matching
- **Error** ❌ - Processing failed

### Resume Actions

- **View Details** - See parsed information
- **Download** - Get original file
- **Reprocess** - Re-run analysis
- **Delete** - Remove from system

## Candidate Matching

### Matching Strategies

#### Standard (Recommended)
- Full scoring analysis
- All components evaluated
- Processing time: 2-5 min per 100 resumes
- Best for: Most use cases

#### Fast
- Vector similarity search
- Processing time: 30-60 sec per 100 resumes
- Best for: Large candidate pools

#### Comprehensive
- Standard + bias detection
- Additional analysis
- Processing time: 5-10 min per 100 resumes
- Best for: Compliance-focused hiring

### Matching Configuration

#### Custom Weights

Adjust scoring weights:

```json
{
  "skills": 0.60,      // 60% weight
  "experience": 0.25,  // 25% weight
  "education": 0.15   // 15% weight
}
```

#### Diversity Weight

Balance merit vs diversity:

- **0.0** - Pure merit-based (default)
- **0.1** - Slight diversity consideration
- **0.5** - Balanced approach
- **1.0** - Maximum diversity

#### Bias Detection

Enable to get:
- Gender bias analysis
- Age bias detection
- Institution bias review
- Recommendations for improvement

### Viewing Results

#### Ranked List View

- Sortable columns
- Filter by score range
- Search functionality
- Export options

#### Candidate Detail View

- **Score Breakdown:**
  - Overall score
  - Component scores
  - Visual charts

- **Resume Information:**
  - Skills list
  - Experience timeline
  - Education details

- **Match Explanation:**
  - Why they matched
  - Strengths highlighted
  - Potential concerns

#### Comparison View

Compare multiple candidates:
- Side-by-side scores
- Skill overlap
- Experience comparison
- Education comparison

## Reports and Analytics

### Match Reports

Generate comprehensive reports:

1. Select job
2. Click "Generate Report"
3. Choose format:
   - **PDF** - Professional report
   - **CSV** - Data analysis
   - **Excel** - Detailed spreadsheet

### Analytics Dashboard

View insights:

- **Match Quality Trends** - Score trends over time
- **Skill Distribution** - Most common skills
- **Experience Levels** - Candidate experience spread
- **Education Breakdown** - Degree distribution

### Export Options

- **CSV Export** - All candidate data
- **PDF Report** - Formatted report
- **Excel Export** - Detailed analysis

## Settings

### Account Settings

- **Profile Information**
  - Email address
  - Display name
  - Timezone

- **Password Management**
  - Change password
  - Two-factor authentication (coming soon)

### Application Settings

- **Default Matching Strategy**
- **Default Score Weights**
- **Notification Preferences**
- **Export Format Preferences**

### Team Settings (Admin)

- **User Management**
  - Add/remove users
  - Assign roles
  - Manage permissions

- **System Configuration**
  - API settings
  - Integration settings
  - Storage configuration

## Keyboard Shortcuts

- **Ctrl/Cmd + K** - Quick search
- **Ctrl/Cmd + N** - New job
- **Ctrl/Cmd + U** - Upload resume
- **Ctrl/Cmd + M** - Start matching
- **Esc** - Close dialogs

## Best Practices

### Job Creation
1. Use clear, specific requirements
2. List all mandatory skills
3. Set realistic experience requirements
4. Update job descriptions regularly

### Resume Upload
1. Upload in batches for efficiency
2. Ensure files are readable
3. Use standard formats (PDF preferred)
4. Keep file sizes reasonable

### Matching
1. Review bias detection recommendations
2. Adjust weights based on role importance
3. Export results for team review
4. Document matching decisions

## See Also

- [Getting Started Guide](./getting-started.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [FAQ](./faq.md)

