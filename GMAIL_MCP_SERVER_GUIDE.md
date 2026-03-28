# Gmail MCP Server Guide

## 🎉 What is Gmail MCP Server?

A **standalone MCP (Model Context Protocol) server** for Gmail operations that can be used by:
- **Claude Code** - Direct tool calls
- **Orchestrator** - Send approved emails
- **Any MCP client** - Standard MCP protocol

---

## 🚀 Quick Start

### 1. Authenticate (First Time)

```bash
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\gmail_mcp_server.py --auth
```

This will:
- Open browser for Gmail authentication
- Save token to `src/token_gmail_mcp.json`
- Ready to send emails!

### 2. Test It

```bash
# List drafts
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\gmail_mcp_server.py --test

# Send test email
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\gmail_mcp_server.py --send
```

### 3. Run as MCP Server

```bash
# As standalone MCP server
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\gmail_mcp_server.py
```

---

## 🔧 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| **send_email** | Send email immediately | `to`, `subject`, `body`, `from` (optional) |
| **create_draft** | Create draft for review | `to`, `subject`, `body`, `from` (optional) |
| **list_drafts** | List email drafts | `max_results` (default: 10) |
| **search_emails** | Search Gmail | `query`, `max_results` (default: 10) |

---

## 📋 Usage Examples

### Send Email (Direct Python)

```python
from gmail_mcp_server import GmailMCPServer

mcp = GmailMCPServer()
mcp.authenticate()

result = mcp.send_email(
    to="someone@example.com",
    subject="Hello",
    body="This is a test email"
)

print(result)
# Output: {"success": True, "message_id": "19d15xxx", ...}
```

### Use with Claude Code

```bash
# Start Claude Code with Gmail MCP
claude --mcp "python src/gmail_mcp_server.py"

# Then in Claude:
"Send an email to test@example.com with subject 'Meeting' and body 'Let's meet tomorrow'"
```

### Orchestrator Integration

The orchestrator now automatically uses Gmail MCP Server:

```
Approval → Orchestrator → Gmail MCP → Email Sent ✅
```

---

## 🎯 Workflow Integration

### Email Approval Workflow

```
1. Gmail Watcher detects email
   ↓
2. AI creates draft response
   ↓
3. Creates approval file
   ↓
4. You approve in Web UI
   ↓
5. Orchestrator calls Gmail MCP Server
   ↓
6. ✅ Email sent via Gmail API
```

### Direct MCP Usage

```
Claude Code → Gmail MCP Server → Gmail API → Email Sent
```

---

## 🔐 Authentication

**First time:**
```bash
python src/gmail_mcp_server.py --auth
```

**Token location:**
- File: `src/token_gmail_mcp.json`
- Contains: OAuth 2.0 credentials
- **Never commit to git!**

**Re-authenticate:**
```bash
del src\token_gmail_mcp.json
python src/gmail_mcp_server.py --auth
```

---

## 📊 MCP Server Configuration

### For Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "C:\\Users\\LENOVO\\AppData\\Local\\Programs\\Python\\Python314\\python.exe",
      "args": ["src/gmail_mcp_server.py"],
      "cwd": "C:\\Users\\LENOVO\\Desktop\\ai-employee\\AI-Employee"
    }
  }
}
```

### For Other MCP Clients

```json
{
  "gmail": {
    "command": "python",
    "args": ["gmail_mcp_server.py"],
    "cwd": "/path/to/AI-Employee"
  }
}
```

---

## 🧪 Testing

### Test All Tools

```python
from gmail_mcp_server import GmailMCPServer
import json

mcp = GmailMCPServer()
mcp.authenticate()

# Test send_email
print("Testing send_email...")
result = mcp.send_email(
    to="your_email@gmail.com",
    subject="MCP Test",
    body="This is a test from Gmail MCP Server"
)
print(json.dumps(result, indent=2))

# Test list_drafts
print("\nTesting list_drafts...")
result = mcp.list_drafts()
print(json.dumps(result, indent=2))

# Test search_emails
print("\nTesting search_emails...")
result = mcp.search_emails(query="is:inbox", max_results=5)
print(json.dumps(result, indent=2))
```

---

## 🎯 Current Integration

Your AI Employee now uses Gmail MCP Server:

✅ **Orchestrator** → Sends approved emails via MCP
✅ **Standalone** → Can be used independently
✅ **Claude Code** → Can be configured as MCP server
✅ **Standard Protocol** → Works with any MCP client

---

## 📚 API Reference

### `send_email(to, subject, body, from=None)`

Send an email.

**Returns:**
```json
{
  "success": true,
  "message_id": "19d15xxx",
  "thread_id": "19d15xxx",
  "status": "sent"
}
```

### `create_draft(to, subject, body, from=None)`

Create a draft.

**Returns:**
```json
{
  "success": true,
  "draft_id": "r-xxx",
  "message_id": "19d15xxx"
}
```

### `list_drafts(max_results=10)`

List drafts.

**Returns:**
```json
{
  "success": true,
  "drafts": [
    {
      "draft_id": "r-xxx",
      "subject": "Re: Meeting",
      "to": "someone@example.com"
    }
  ]
}
```

### `search_emails(query, max_results=10)`

Search emails.

**Returns:**
```json
{
  "success": true,
  "emails": [
    {
      "id": "19d15xxx",
      "subject": "Meeting",
      "from": "someone@example.com",
      "date": "Mon, 22 Mar 2026 12:00:00 GMT",
      "snippet": "Let's meet tomorrow..."
    }
  ]
}
```

---

## 🎉 You're All Set!

Your AI Employee now has a **proper Gmail MCP Server** that:

✅ Sends emails via MCP protocol
✅ Works with orchestrator
✅ Can be used by Claude Code
✅ Follows MCP standards
✅ Supports multiple tools

**Test it now:**
```bash
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\gmail_mcp_server.py --auth
```

Then approve an email and watch it get sent via MCP! 🚀

---

*Built with ❤️ for AI Employee Silver Tier*
