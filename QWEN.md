# AI-Employee Project Context

## Project Overview

This project is a **Bronze Tier implementation** of the **Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026**.

It provides a foundation layer for an autonomous AI agent that uses:
- **Obsidian** as the knowledge base and dashboard (local-first, privacy-centric)
- **Claude Code** as the reasoning engine
- **Python Watchers** as the perception layer (file system monitoring)
- **Human-in-the-Loop** approval workflow for safety

### Architecture: Perception → Reasoning → Action

```
External Sources (Files, Email, WhatsApp, Bank)
              ↓
    ┌─────────────────┐
    │  Watchers       │  ← Perception Layer
    │  (Python)       │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  Obsidian Vault │  ← Memory/GUI
    │  - Dashboard.md │
    │  - Handbook.md  │
    │  - Needs_Action/│
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  Claude Code    │  ← Reasoning Layer
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  Human Approval │  ← HITL Safety
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  MCP Servers    │  ← Action Layer (Silver+)
    └─────────────────┘
```

## Directory Structure

```
AI-Employee/
├── AI_Employee_Vault/          # Obsidian vault
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Quarterly objectives
│   ├── Inbox/                  # Raw incoming items
│   │   └── Drop/               # File drop folder
│   ├── Needs_Action/           # Items requiring AI processing
│   ├── Plans/                  # AI-generated action plans
│   ├── Pending_Approval/       # Awaiting human approval
│   ├── Approved/               # Ready for execution
│   ├── Rejected/               # Declined actions
│   ├── Done/                   # Completed items
│   ├── Logs/                   # Audit logs (JSON)
│   └── Accounting/             # Financial records
│
├── src/                        # Python source code
│   ├── base_watcher.py         # Abstract base class for watchers
│   ├── filesystem_watcher.py   # File drop folder watcher
│   ├── orchestrator.py         # Master orchestration process
│   ├── watchdog.py             # Health monitor
│   └── retry_handler.py        # Error recovery utilities
│
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # Setup instructions
```

## Bronze Tier Deliverables (Complete)

- [x] **Obsidian vault** with Dashboard.md, Company_Handbook.md, Business_Goals.md
- [x] **One working Watcher script** (File System Watcher)
- [x] **Claude Code integration** for reading/writing to vault
- [x] **Basic folder structure**: /Inbox, /Needs_Action, /Done, /Plans, etc.
- [x] **Orchestrator** for coordinating components
- [x] **Watchdog** for health monitoring
- [x] **Audit logging** in required format
- [x] **Human-in-the-Loop** approval workflow design

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers (Silver/Gold tier) |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Claude Code | Latest | Primary reasoning engine |

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Starting the System

```bash
# Option 1: Start Orchestrator (recommended)
python src/orchestrator.py AI_Employee_Vault

# Option 2: Start Watchdog (auto-restart on crash)
python src/watchdog.py AI_Employee_Vault

# Option 3: Run once (testing)
python src/orchestrator.py AI_Employee_Vault --once

# Check watchdog status
python src/watchdog.py AI_Employee_Vault --status
```

### Using the File System Watcher

1. **Drop a file** into: `AI_Employee_Vault/Inbox/Drop/your_file.txt`
2. **Watcher detects** and creates action file in `Needs_Action/`
3. **Orchestrator processes** and creates plan in `Plans/`
4. **Claude Code** can be invoked: `claude --cwd AI_Employee_Vault`
5. **Human approves** by moving files from `Pending_Approval` to `Approved`
6. **Orchestrator executes** and moves to `Done/`

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/orchestrator.py` | Master coordination process |
| `src/watchdog.py` | Health monitor with auto-restart |
| `src/filesystem_watcher.py` | File drop folder monitoring |
| `src/base_watcher.py` | Abstract base class for all watchers |
| `src/retry_handler.py` | Error recovery with exponential backoff |
| `AI_Employee_Vault/Dashboard.md` | Real-time system status |
| `AI_Employee_Vault/Company_Handbook.md` | Rules of engagement |
| `AI_Employee_Vault/Business_Goals.md` | Quarterly objectives |

## Development Conventions

### Security

- **NEVER** commit `.env` files or credentials
- Use environment variables for API keys
- Use system keychain for sensitive data
- All actions logged to `Logs/YYYY-MM-DD.json`

### Audit Log Format

```json
{
  "timestamp": "2026-03-18T10:30:00",
  "action_type": "file_drop_processed",
  "actor": "filesystem_watcher",
  "target": "document.pdf",
  "result": "success"
}
```

### Human-in-the-Loop

Always requires human approval for:
- Payments to new recipients
- Payments over $100
- Emails to unknown contacts
- Bulk communications
- Irreversible actions

## Upgrading to Silver Tier

To add Silver Tier features:
1. Implement `gmail_watcher.py` using Google API
2. Implement WhatsApp watcher using Playwright
3. Set up email MCP server for sending
4. Add scheduling via cron/Task Scheduler

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Watcher not detecting files | Check drop folder exists, verify permissions |
| Orchestrator not processing | Ensure files have `.md` extension in `Needs_Action/` |
| Unicode errors on Windows | Fixed with explicit UTF-8 encoding |
| Module not found | Run `pip install -r requirements.txt` |

## Hackathon Submission

**Tier**: Bronze - Foundation (Minimum Viable Deliverable)

**Features Implemented**:
- Obsidian vault with complete structure
- File System Watcher for local file drops
- Orchestrator for coordination
- Watchdog for health monitoring
- Audit logging
- HITL approval workflow

**Security Disclosure**:
- Credentials via environment variables
- Dry run mode available
- Full audit trail
- HITL for sensitive actions

---

*Built for the Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026*
