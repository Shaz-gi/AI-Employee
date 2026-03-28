# AI Employee - Silver Tier 🥈

> **Tagline**: Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

A Personal AI Employee implementation for the **Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026**.

---

## 🏆 Tier Status: SILVER TIER COMPLETE

This implementation satisfies all **Silver Tier** requirements:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| All Bronze requirements | ✅ | Foundation layer complete |
| Two or more Watcher scripts | ✅ | File System + Gmail + LinkedIn |
| Auto-post on LinkedIn | ✅ | LinkedIn Poster with AI generation |
| AI reasoning loop | ✅ | OpenRouter Brain integration |
| One working MCP server | ✅ | Email MCP for Gmail |
| HITL approval workflow | ✅ | Pending_Approval folder system |
| Basic scheduling | ✅ | Windows Task Scheduler / cron |
| All AI as Agent Skills | ✅ | Modular skill architecture |

---

## 🚀 What's New in Silver Tier

### 📧 Gmail Integration
- **Gmail Watcher** - Monitors inbox every 2 minutes
- **Important email detection** - Filters by keywords
- **Auto-drafting** - AI drafts responses for approval

### 📤 Email Sending
- **Email MCP Server** - Send via Gmail API
- **Approval workflow** - Human approves before sending
- **Draft management** - Create and review drafts

### 💼 LinkedIn Automation
- **Auto-posting** - Generate posts from Business_Goals.md
- **Session management** - Persistent login
- **Engagement tracking** - Monitor post performance

### ⏰ Task Scheduling
- **Daily Briefing** - 8 AM CEO briefing generation
- **Regular checks** - Gmail every 15 minutes
- **LinkedIn posts** - 9 AM weekdays
- **Orchestrator** - Runs every 5 minutes

---

## 📁 Project Structure

```
AI-Employee/
├── AI_Employee_Vault/          # Obsidian vault
│   ├── Dashboard.md            # Real-time status
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Quarterly objectives
│   ├── Inbox/
│   │   └── Drop/               # File drop folder
│   ├── Needs_Action/           # Items for AI processing
│   ├── Plans/                  # AI-generated plans
│   ├── Pending_Approval/       # Awaiting human approval
│   ├── Approved/               # Ready for execution
│   ├── Rejected/               # Declined actions
│   ├── Done/                   # Completed items
│   ├── Logs/                   # Audit logs
│   └── Accounting/             # Financial records
│
├── src/                        # Python source code
│   # Bronze Tier
│   ├── base_watcher.py         # Abstract base class
│   ├── filesystem_watcher.py   # File drop monitoring
│   ├── orchestrator.py         # Master orchestration
│   ├── watchdog.py             # Health monitor
│   ├── retry_handler.py        # Error recovery
│   ├── openrouter_brain.py     # AI reasoning (OpenRouter)
│   # Silver Tier
│   ├── gmail_watcher.py        # Gmail monitoring ⭐ NEW
│   ├── email_mcp.py            # Email sending ⭐ NEW
│   ├── linkedin_poster.py      # LinkedIn automation ⭐ NEW
│   └── scheduler.py            # Task scheduling ⭐ NEW
│
├── .env                        # Environment variables
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── SILVER_TIER_SETUP.md        # Detailed setup guide
```

---

## 🛠️ Setup Guide

### Quick Setup (15 minutes)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Get API Keys**
   - OpenRouter: https://openrouter.ai/keys
   - Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com

3. **Configure .env**
   ```bash
   cp .env.example .env
   # Edit with your keys
   ```

4. **Authenticate services**
   ```bash
   python src/gmail_watcher.py AI_Employee_Vault --auth
   python src/email_mcp.py --auth
   python src/linkedin_poster.py --login
   ```

5. **Install scheduled tasks**
   ```bash
   python src/scheduler.py install
   ```

**Full setup guide:** See `SILVER_TIER_SETUP.md`

---

## 📊 Usage Examples

### Monitor Gmail

```bash
# Run Gmail Watcher
python src/gmail_watcher.py AI_Employee_Vault

# Action files created in Needs_Action/
# AI drafts responses
# Approval files created in Pending_Approval/
```

### Send Email

```bash
# Send test email
python src/email_mcp.py --send

# MCP server mode (for Claude Code)
python src/email_mcp.py
```

### Post to LinkedIn

```bash
# Generate post from Business_Goals.md
python src/linkedin_poster.py --generate --vault AI_Employee_Vault

# Post custom content
python src/linkedin_poster.py --post "Business update! #Growth"

# With image
python src/linkedin_poster.py --post "Update!" --image image.png
```

### Manage Scheduled Tasks

```bash
# Install all tasks
python src/scheduler.py install

# View status
python src/scheduler.py status

# Remove tasks
python src/scheduler.py remove

# Run daily briefing manually
python src/scheduler.py run daily-briefing
```

---

## 🔄 Workflow Examples

### Email Response Flow

```
📧 New email arrives
   ↓
👁️ Gmail Watcher detects (every 2 min)
   ↓
📄 Creates action file in Needs_Action/
   ↓
🤖 AI processes and drafts response
   ↓
📋 Creates approval file in Pending_Approval/
   ↓
👤 Human reviews in Obsidian
   ↓
✅ Move to Approved/ to send
   ↓
📤 Email MCP sends email
   ↓
📁 File moved to Done/
```

### LinkedIn Auto-Post Flow

```
⏰ 9:00 AM weekday (scheduled)
   ↓
📝 LinkedIn Poster reads Business_Goals.md
   ↓
🤖 AI generates post content
   ↓
🔗 Posts to LinkedIn automatically
   ↓
📊 Logs engagement metrics
   ↓
📁 Updates Dashboard
```

### Daily CEO Briefing

```
⏰ 8:00 AM daily (scheduled)
   ↓
🤖 Orchestrator generates briefing
   ↓
📊 Reviews: Bank, Tasks, Goals, Metrics
   ↓
📄 Creates briefing in Briefings/
   ↓
📢 Updates Dashboard.md
   ↓
👤 CEO reviews over morning coffee ☕
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# OpenRouter (AI Brain)
OPENROUTER_API_KEY=sk-or-v1-your_key
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free

# Gmail API
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# LinkedIn
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password

# Scheduling
WATCHER_CHECK_INTERVAL=120
WATCHDOG_CHECK_INTERVAL=60
```

### Scheduled Tasks

| Task | Schedule | Command |
|------|----------|---------|
| Daily Briefing | 8:00 AM daily | `orchestrator.py --once` |
| Gmail Check | Every 15 min | `gmail_watcher.py` |
| LinkedIn Post | 9:00 AM (weekdays) | `linkedin_poster.py --generate` |
| Orchestrator | Every 5 min | `orchestrator.py` |

---

## 🆘 Troubleshooting

### Gmail Authentication Failed

```bash
# Delete token and re-authenticate
del src\token.json
python src/gmail_watcher.py AI_Employee_Vault --auth
```

### LinkedIn Login Issues

- LinkedIn may block automated logins
- Use session from successful login
- Consider manual posting with AI-generated content

### Scheduled Task Not Running

**Windows:**
```bash
# Open Task Scheduler
taskschd.msc
# Check "Last Run Result" (should be 0x0)
```

**Linux/Mac:**
```bash
# Check cron
crontab -l
# View logs
grep CRON /var/log/syslog
```

### OpenRouter Model Unavailable

```bash
# Check available models
python check_openrouter_models.py

# Update .env with working model
OPENROUTER_MODEL=google/gemma-3n-e4b-it:free
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | This file - overview |
| **SILVER_TIER_SETUP.md** | Detailed setup guide |
| **SILVER_TIER_COMPLETE.md** | Feature checklist |
| **COMMANDS.md** | All commands reference |
| **QUICKSTART.md** | 5-minute quick start |

---

## ✅ Silver Tier Checklist

- [x] Gmail Watcher implemented
- [x] Email MCP Server implemented
- [x] LinkedIn Poster implemented
- [x] Task Scheduler implemented
- [x] Approval workflow from Bronze
- [x] AI reasoning with OpenRouter
- [x] File System Watcher from Bronze
- [x] Orchestrator updated
- [x] Documentation complete

---

## 🎯 Next: Gold Tier

Ready for more? Gold Tier adds:
- **Odoo Integration** - Full accounting system
- **Facebook/Instagram** - Social media automation
- **Twitter/X Integration** - Auto-posting and monitoring
- **Weekly Business Audit** - Comprehensive reports
- **Multi-domain integration** - Personal + Business

---

*Silver Tier - Functional Assistant*
*Built for Personal AI Employee Hackathon 0*
