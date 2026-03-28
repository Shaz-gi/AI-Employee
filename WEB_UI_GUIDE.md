# 🎨 AI Employee Web UI - User Guide

## 🚀 Access Your Dashboard

**Open in your browser:**
```
http://localhost:5000
```

Or double-click: `start_web_ui.bat`

---

## 📊 Dashboard Features

### 1. **Dashboard Tab** 📈
- **Real-time statistics** - See counts for all folders
- **Recent activity log** - View what the AI has been doing
- **Quick actions** - Run orchestrator manually

### 2. **Emails Tab** 📧
- **View all emails** detected by Gmail Watcher
- **Priority indicators** (Red = High, Yellow = Medium)
- **Click to read** full email content
- **Sorted by priority** - High priority emails first

### 3. **Approvals Tab** ✅
- **View pending approvals** - Items waiting for your review
- **One-click approve** - Move to Approved folder
- **One-click reject** - Move to Rejected folder
- **Summary view** - Quick overview of what needs approval

### 4. **LinkedIn Tab** 💼
- **Generate posts** from your Business_Goals.md
- **AI-powered content** - Automatically created
- **Copy to clipboard** - Ready to paste on LinkedIn

### 5. **Send Email Tab** ✉️
- **Compose emails** directly from the dashboard
- **Send via Gmail API** - Uses your authenticated account
- **Instant delivery** - No approval needed (you're approving by sending)

---

## 🎯 Daily Workflow

### Morning Routine (5 minutes)

1. **Open Dashboard** - http://localhost:5000
2. **Check Stats** - See what came in overnight
3. **Review Approvals** - Approve/reject pending items
4. **Generate LinkedIn Post** - Post to LinkedIn manually

### During the Day

1. **Monitor Emails** - Check Emails tab for new messages
2. **Send Replies** - Use Send Email tab for quick responses
3. **Run Orchestrator** - If you want immediate processing

### Evening Review (2 minutes)

1. **Check Completed** - See what was done today
2. **Review Activity Log** - Audit trail of all actions

---

## 🎨 UI Features

### Modern Dark Theme
- Easy on the eyes
- Professional look
- Color-coded priorities

### Responsive Design
- Works on desktop
- Works on tablet
- Mobile-friendly

### Real-time Updates
- Auto-refreshes every 30 seconds
- Manual refresh button available
- Live statistics

---

## 🔧 Troubleshooting

### Can't Access Dashboard?

1. **Check if server is running**
   - Look for: "Running on http://localhost:5000"
   
2. **Restart the server**
   - Close any running instance
   - Double-click `start_web_ui.bat`

3. **Check port is free**
   - Port 5000 might be in use
   - Edit `app.py` and change `port=5000` to another port

### Emails Not Showing?

1. **Gmail Watcher may not have run**
   - Run manually: `python src/gmail_watcher.py AI_Employee_Vault`
   
2. **Check token exists**
   - File: `src/token.json`
   - Re-authenticate if missing

### Approvals Empty?

- This is good! It means nothing needs approval
- Or AI didn't find anything requiring approval
- Run orchestrator to process pending items

---

## 📱 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F5` | Refresh dashboard |
| `Esc` | Close modal |
| `Tab` | Navigate buttons |

---

## 🎯 Pro Tips

1. **Keep dashboard open** - Auto-refreshes with latest data
2. **Use approvals tab daily** - Don't let items pile up
3. **Generate LinkedIn posts weekly** - Keep your network updated
4. **Check activity log** - Understand what AI is doing

---

## 🆘 Quick Commands

```bash
# Start Web UI
start_web_ui.bat

# Start Orchestrator
python src\orchestrator.py AI_Employee_Vault

# Check Gmail manually
python src\gmail_watcher.py AI_Employee_Vault

# Generate LinkedIn post
python src\linkedin_poster.py --generate --vault AI_Employee_Vault
```

---

## 🎉 You're All Set!

Your AI Employee now has a beautiful, modern web interface!

**Access it at:** http://localhost:5000

---

*Built with ❤️ for AI Employee Silver Tier*
