# Silver Tier Setup Guide

## 🎉 Welcome to Silver Tier!

Silver Tier transforms your AI Employee from a foundation into a **functional assistant** with:
- Email monitoring (Gmail)
- Auto-posting to LinkedIn
- Scheduled tasks
- Email sending capability

---

## 📋 Silver Tier Deliverables

| Feature | Status | Description |
|---------|--------|-------------|
| **Gmail Watcher** | ✅ | Monitor Gmail for new emails |
| **Email MCP Server** | ✅ | Send emails via Gmail API |
| **LinkedIn Poster** | ✅ | Auto-post business updates |
| **Task Scheduler** | ✅ | Schedule daily briefings and tasks |
| **Approval Workflow** | ✅ | From Bronze Tier |
| **AI Reasoning** | ✅ | From Bronze Tier |

---

## 🚀 Quick Start

### Step 1: Install Silver Tier Dependencies

```bash
cd AI-Employee
pip install -r requirements.txt
playwright install  # For LinkedIn automation
```

### Step 2: Setup Gmail API

1. **Enable Gmail API**
   - Visit: https://console.cloud.google.com/apis/library/gmail.googleapis.com
   - Create a new project or select existing
   - Enable the API

2. **Create OAuth Credentials**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download as `credentials.json`
   - Place in `src/` folder

3. **Add Gmail Scopes**
   - In Google Cloud Console, go to "OAuth consent screen"
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.draft`

4. **Authenticate Gmail**
   ```bash
   python src/gmail_watcher.py AI_Employee_Vault --auth
   python src/email_mcp.py --auth
   ```

### Step 3: Setup LinkedIn

1. **Set Credentials** (securely)
   ```bash
   # Windows (PowerShell)
   $env:LINKEDIN_EMAIL="your@email.com"
   $env:LINKEDIN_PASSWORD="your_password"
   
   # Or add to .env file (not recommended for production)
   ```

2. **Login to LinkedIn**
   ```bash
   python src/linkedin_poster.py --login
   ```

### Step 4: Install Scheduled Tasks

```bash
# Install all scheduled tasks
python src/scheduler.py install --vault AI_Employee_Vault

# Check status
python src/scheduler.py status
```

---

## 📁 New Files in Silver Tier

```
src/
├── gmail_watcher.py       # Monitor Gmail for new emails
├── email_mcp.py           # Send emails via Gmail
├── linkedin_poster.py     # Post to LinkedIn
└── scheduler.py           # Task scheduling
```

---

## 🔧 Configuration

### .env File Updates

```env
# Gmail API (optional - credentials.json is used)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# LinkedIn (for automated posting)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# OpenRouter (AI Brain)
OPENROUTER_API_KEY=sk-or-v1-your_key
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
```

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| **Daily Briefing** | 8:00 AM daily | Generate CEO briefing |
| **Gmail Check** | Every 15 min | Check for new emails |
| **LinkedIn Post** | 9:00 AM (weekdays) | Post business update |
| **Orchestrator** | Every 5 min | Process action files |

---

## 📊 Usage Examples

### Check Gmail Manually

```bash
python src/gmail_watcher.py AI_Employee_Vault
```

### Send an Email

```bash
python src/email_mcp.py --send
```

### Post to LinkedIn

```bash
# Generate post from Business_Goals.md
python src/linkedin_poster.py --generate --vault AI_Employee_Vault

# Post custom content
python src/linkedin_poster.py --post "Exciting business update! #Growth"
```

### Manage Scheduled Tasks

```bash
# Install all tasks
python src/scheduler.py install

# Remove all tasks
python src/scheduler.py remove

# Check status
python src/scheduler.py status

# Run daily briefing manually
python src/scheduler.py run daily-briefing
```

---

## 🎯 Workflow Examples

### 1. Email Response Workflow

```
1. Gmail receives new email
   ↓
2. Gmail Watcher detects it
   ↓
3. Creates action file in Needs_Action/
   ↓
4. Orchestrator processes with AI
   ↓
5. Creates draft response + approval file
   ↓
6. Human reviews in Pending_Approval/
   ↓
7. Moves to Approved/
   ↓
8. Email MCP sends email
   ↓
9. File moved to Done/
```

### 2. LinkedIn Auto-Posting Workflow

```
1. Scheduled task runs at 9 AM
   ↓
2. LinkedIn Poster reads Business_Goals.md
   ↓
3. AI generates post content
   ↓
4. Posts to LinkedIn automatically
   ↓
5. Logs engagement metrics
```

### 3. Daily CEO Briefing

```
1. Scheduled task runs at 8 AM
   ↓
2. Orchestrator generates briefing
   ↓
3. Reviews: Bank transactions, Tasks, Goals
   ↓
4. Creates briefing in Briefings/
   ↓
5. Notifies human via dashboard update
```

---

## 🆘 Troubleshooting

### Gmail Authentication Failed

```bash
# Delete token and re-authenticate
del src\token.json
python src/gmail_watcher.py AI_Employee_Vault --auth
```

### LinkedIn Login Fails

- LinkedIn may block automated logins
- Use session file from successful login
- Consider manual posting for now

### Scheduled Task Not Running

**Windows:**
```bash
# Open Task Scheduler
taskschd.msc

# Find task and check "Last Run Result"
# Should be 0x0 (success)
```

**Linux/Mac:**
```bash
# Check cron logs
grep CRON /var/log/syslog

# List crontab
crontab -l
```

### Playwright Browser Issues

```bash
# Reinstall browsers
playwright install chromium

# Test installation
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

---

## 📚 API Setup Guides

### Google Cloud Console Setup

1. **Create Project**
   - https://console.cloud.google.com
   - New Project → "AI Employee"

2. **Enable APIs**
   - Gmail API
   - Google Drive API (optional)

3. **Create OAuth Credentials**
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Download as `credentials.json`

4. **Publish OAuth Consent Screen**
   - Test mode is fine for development
   - Add your email as test user

### LinkedIn Automation Notes

⚠️ **Important**: LinkedIn's Terms of Service may restrict automation. Use at your own risk.

Alternatives:
- Manual posting with AI-generated content
- Use LinkedIn API (requires business account)
- Schedule posts via Buffer/Hootsuite

---

## ✅ Silver Tier Checklist

- [ ] Gmail API credentials setup
- [ ] Gmail Watcher authenticated
- [ ] Email MCP authenticated
- [ ] LinkedIn credentials configured
- [ ] LinkedIn login successful
- [ ] Scheduled tasks installed
- [ ] Daily briefing scheduled
- [ ] Test email sent successfully
- [ ] Test LinkedIn post created
- [ ] All watchers running

---

## 🎯 Next Steps: Gold Tier

After mastering Silver Tier, consider:
- **Odoo Integration** - Accounting system
- **Facebook/Instagram** - Social media automation
- **Twitter/X Integration** - Auto-posting
- **Weekly Business Audit** - Comprehensive reports
- **Error Recovery** - Graceful degradation

---

*Silver Tier - Functional Assistant*
*Built for Personal AI Employee Hackathon 0*
