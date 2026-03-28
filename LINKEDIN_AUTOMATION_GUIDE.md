# 🤖 AI-Powered LinkedIn Automation

## Overview

Your AI Employee now automatically:
1. **Generates LinkedIn posts** from your Business_Goals.md using AI
2. **Requires your approval** before posting anything
3. **Schedules posts** at optimal times (9 AM, 12 PM, 5 PM)
4. **Auto-posts** approved content to LinkedIn
5. **Varies content types** daily (insights, achievements, questions, tips, motivation)

---

## 🎯 Features

### AI Post Generation
- Reads your `Business_Goals.md` file
- Generates 5 different post types automatically
- Creates engaging, professional content
- Includes relevant hashtags

### Approval Workflow
- All AI-generated posts require approval
- Review in the LinkedIn dashboard (`/linkedin`)
- Approve or reject with one click
- Posts are scheduled automatically after approval

### Auto-Posting
- Approved posts are published automatically
- Uses browser automation (Playwright)
- Saves LinkedIn session for reuse
- Tracks posted content in database

### Daily Scheduling
- Generates posts daily at 8 AM
- Schedules at optimal times:
  - **9:00 AM** - Morning commute
  - **12:00 PM** - Lunch break
  - **5:00 PM** - End of workday
- Varies post types for diversity

---

## 📋 Setup

### 1. Database Migration

Run this SQL in **Supabase SQL Editor**:

```bash
# File location:
D:\ai-employee\AI-Employee\linkedin_posts_migration.sql
```

**Copy all content → Paste in SQL Editor → Click Run**

This creates:
- `linkedin_posts` table
- Indexes for performance
- Row-level security policies
- Auto-updating timestamps

---

### 2. Configure LinkedIn Credentials

Set environment variables:

**Windows (add to `.env` or System Properties):**
```env
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
```

**Or set via System Properties:**
1. Search "Environment Variables" in Windows
2. Add new user variables:
   - `LINKEDIN_EMAIL` = your LinkedIn email
   - `LINKEDIN_PASSWORD` = your LinkedIn password

---

### 3. Test LinkedIn Connection

```bash
cd D:\ai-employee\AI-Employee
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\linkedin_auto_post.py --login
```

**First time:** Browser will open - log in manually
**Next times:** Session is saved, auto-login works

---

### 4. Start LinkedIn Scheduler

**Option A: Run manually**
```bash
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\linkedin_scheduler.py
```

**Option B: Run as background service (Recommended)**

Create `start_linkedin_scheduler.bat`:
```batch
@echo off
set LINKEDIN_EMAIL=your.email@example.com
set LINKEDIN_PASSWORD=your_password
set OPENROUTER_API_KEY=sk-or-v1-xxx
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key

cd /d "D:\ai-employee\AI-Employee"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\linkedin_scheduler.py
```

**Run it:**
```bash
start_linkedin_scheduler.bat
```

**Or schedule with Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task → "LinkedIn Scheduler"
3. Trigger: At startup
4. Action: Start a program → `start_linkedin_scheduler.bat`
5. Finish

---

## 🚀 Usage

### Generate Posts Manually

```bash
# Generate one post
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\ai_linkedin_generator.py

# Generate 5 posts for the week
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\ai_linkedin_generator.py --count 5

# Generate specific type
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\ai_linkedin_generator.py --type insight
```

### Post Types

| Type | Description | Example |
|------|-------------|---------|
| **insight** | Business lessons | "Here's what I learned about..." |
| **achievement** | Celebrating wins | "Excited to share..." |
| **question** | Engaging audience | "What's your biggest challenge with...?" |
| **tip** | Helpful advice | "Pro tip: Try this..." |
| **motivation** | Inspirational | "Remember: Progress over perfection" |

---

### Approve Posts in UI

1. **Go to:** `http://localhost:3000/linkedin`
2. **Click:** "AI Generate" button (purple sparkle)
3. **Wait:** AI generates post from Business_Goals.md
4. **Review:** See generated post in dashboard
5. **Approve:** Click "Approve" button
6. **Posted:** Scheduler auto-posts within 5 minutes

**Or manually create:**
1. Click "New Post"
2. Write content
3. Schedule for later or post now

---

## 📊 Dashboard Features

### Stats Cards
- **Total** - All posts
- **Pending** - Awaiting your approval
- **Approved** - Ready to post
- **Scheduled** - Queued for specific time
- **Posted** - Published to LinkedIn

### Post Actions
- **Approve** - Schedule for posting
- **Reject** - Discard post
- **View** - See full details
- **Delete** - Remove permanently

### AI Generate Modal
Shows:
- How AI generation works
- Post type options
- Generation progress

---

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────┐
│  Daily at 8 AM                                          │
│  ↓                                                      │
│  AI reads Business_Goals.md                            │
│  ↓                                                      │
│  Generates 5 posts (different types)                   │
│  ↓                                                      │
│  Saves to database as "pending_approval"               │
│  ↓                                                      │
│  ┌──────────────────────────────────────────────┐     │
│  │           WAITING FOR APPROVAL               │     │
│  └──────────────────────────────────────────────┘     │
│  ↓                                                      │
│  You review in LinkedIn dashboard                      │
│  ↓                                                      │
│  Click "Approve"                                       │
│  ↓                                                      │
│  Status changes to "approved"                          │
│  ↓                                                      │
│  Scheduler detects approved post (every 5 min)         │
│  ↓                                                      │
│  Checks scheduled time                                 │
│  ↓                                                      │
│  Posts to LinkedIn automatically                       │
│  ↓                                                      │
│  Updates status to "posted"                            │
│  ↓                                                      │
│  Done! ✅                                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Commands Reference

### AI Generator
```bash
# Generate one post
python src/ai_linkedin_generator.py

# Generate multiple posts
python src/ai_linkedin_generator.py --count 5

# Specific type
python src/ai_linkedin_generator.py --type motivation

# Save to database only
python src/ai_linkedin_generator.py --user-id YOUR_USER_ID
```

### Scheduler
```bash
# Run scheduler (continuous)
python src/linkedin_scheduler.py

# Generate only (no posting)
python src/linkedin_scheduler.py --generate-only

# Process approved posts now
python src/linkedin_scheduler.py --post-now
```

### Auto-Poster
```bash
# Post content
python src/linkedin_auto_post.py --content "Your post here"

# Login only
python src/linkedin_auto_post.py --login

# Post from file
python src/linkedin_auto_post.py --file post.txt
```

---

## 📁 File Structure

```
AI-Employee/
├── src/
│   ├── ai_linkedin_generator.py    # AI post generation
│   ├── linkedin_scheduler.py       # Daily scheduler
│   ├── linkedin_auto_post.py       # Browser automation
│   └── linkedin_poster.py          # Legacy poster
├── frontend/src/pages/
│   └── LinkedIn.jsx                # UI dashboard
├── AI_Employee_Vault/
│   └── Business_Goals.md           # Source for AI generation
└── linkedin_posts_migration.sql    # Database setup
```

---

## 🔧 Troubleshooting

### "LinkedIn login failed"
**Solution:**
1. Check credentials are set correctly
2. Try manual login first: `python src/linkedin_auto_post.py --login`
3. Wait for browser to open and log in manually
4. Session will be saved for next time

### "No posts generated"
**Check:**
1. `Business_Goals.md` exists and has content
2. `OPENROUTER_API_KEY` is set
3. Check generator output for errors

### "Posts not auto-posting"
**Check:**
1. Scheduler is running
2. Posts are approved (status = 'approved')
3. Scheduled time has passed
4. LinkedIn credentials are valid

### "Database error"
**Solution:**
1. Run migration SQL in Supabase
2. Check `SUPABASE_URL` and `SUPABASE_KEY` are set
3. Verify table exists: `SELECT * FROM linkedin_posts LIMIT 1;`

---

## 🎯 Best Practices

### Content Quality
1. **Review all AI-generated posts** before approving
2. **Personalize** when needed (add specific details)
3. **Vary post types** for engagement
4. **Post consistently** (daily is ideal)

### Timing
- **Morning (9 AM)** - Insights, motivation
- **Lunch (12 PM)** - Quick tips, questions
- **Evening (5 PM)** - Achievements, reflections

### Approval Workflow
- Check posts **once daily** (morning or evening)
- Approve 2-3 posts at a time
- Reject anything that doesn't feel authentic
- Edit Business_Goals.md to improve future generation

---

## 📈 Success Metrics

Track in LinkedIn dashboard:
- Posts generated per week
- Approval rate (approved / generated)
- Posts published
- Engagement (likes, comments, shares)

**Goal:** 5-7 posts per week, mixed types

---

## 🔐 Security

- LinkedIn credentials stored in environment variables only
- Browser session saved locally (encrypted by OS)
- Database uses Row-Level Security (RLS)
- Service role key required for automated posting

**Never commit:**
- `.env` files
- `credentials.json`
- Browser session data

---

## 🚀 Next Steps

1. **Run database migration** ✅
2. **Set LinkedIn credentials** ✅
3. **Test login** ✅
4. **Start scheduler** ✅
5. **Generate first posts** ✅
6. **Approve and watch them post automatically!** 🎉

---

*Built with ❤️ for the future of work*
