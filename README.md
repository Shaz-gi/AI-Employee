# AI Employee - Bronze Tier

> **Tagline**: Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

A Personal AI Employee implementation for the **Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026**.

This Bronze Tier implementation provides the **foundation layer** for an autonomous AI agent that uses:
- **Obsidian** as the knowledge base and dashboard (local-first, privacy-centric)
- **OpenRouter** as the reasoning engine (FREE API - Qwen, Llama, Mistral models)
- **Python Watchers** as the perception layer (sensing changes in files, emails, etc.)
- **Human-in-the-Loop** approval workflow for safety

---

## Quick Start

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers (for Silver/Gold tier) |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| OpenRouter API Key | **FREE** - No credit card | AI reasoning engine |

### Installation

1. **Clone or download this repository**

2. **Get FREE OpenRouter API Key**
   - Visit: https://openrouter.ai/keys
   - Sign in (Google, GitHub, or Email)
   - Create API Key
   - Copy your key (starts with `sk-or-`)

3. **Install Python dependencies**
   ```bash
   cd AI-Employee
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

5. **Create your Obsidian vault**
   - Open Obsidian
   - Create a new vault pointing to `AI_Employee_Vault/` folder
   - Or use the existing vault structure provided

6. **Verify installation**
   ```bash
   python test_openrouter.py "Hello, can you help me process documents?"
   ```

---

## Architecture

### Perception → Reasoning → Action

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SOURCES                            │
│      Gmail    │    WhatsApp    │    Bank APIs    │    Files     │
└────────┬──────────┬─────────────────┬─────────────────┬─────────┘
         │          │                 │                 │
         ▼          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PERCEPTION LAYER (Watchers)                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │ Gmail Watcher│  │ WhatsApp     │  │ File System  │          │
│   │   (Python)   │  │ Watcher      │  │ Watcher      │          │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└──────────┼─────────────────┼─────────────────┼──────────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OBSIDIAN VAULT (Local)                      │
│   ┌────────────────────────────────────────────────────────┐    │
│   │  /Needs_Action/  │  /Plans/  │  /Done/  │  /Logs/      │    │
│   │  /Pending_Approval/  │  /Approved/  │  /Rejected/     │    │
│   │  Dashboard.md  │  Company_Handbook.md  │  Business_Goals │   │
│   └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REASONING LAYER                             │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    CLAUDE CODE                           │   │
│   │    Read → Think → Plan → Write → Request Approval        │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HUMAN-IN-THE-LOOP                          │
│   ┌──────────────────────┐     ┌──────────────────────┐         │
│   │  Review Approval     │     │  Move to /Approved   │         │
│   │  Files in Obsidian   │────▶│  or /Rejected        │         │
│   └──────────────────────┘     └──────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ACTION LAYER (MCP Servers)                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │   Email MCP  │  │   Browser    │  │   Calendar   │          │
│   │   (Silver+)  │  │   MCP        │  │   MCP        │          │
│   └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Folder Structure

```
AI-Employee/
├── AI_Employee_Vault/          # Obsidian vault (DO NOT commit to git)
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Quarterly objectives
│   ├── Inbox/                  # Raw incoming items
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
└── README.md                   # This file
```

---

## Bronze Tier Deliverables

This implementation satisfies all **Bronze Tier** requirements:

- [x] **Obsidian vault** with Dashboard.md and Company_Handbook.md
- [x] **One working Watcher script** (File System Watcher)
- [x] **Claude Code integration** for reading/writing to vault
- [x] **Basic folder structure**: /Inbox, /Needs_Action, /Done
- [x] **Orchestrator** for coordinating components
- [x] **Watchdog** for health monitoring
- [x] **Audit logging** in required format

---

## Usage

### Starting the System

#### Option 1: Start Orchestrator (Recommended)

```bash
python src/orchestrator.py AI_Employee_Vault
```

This starts:
- File system watcher (monitors drop folder)
- Orchestration cycle (processes files every 30 seconds)
- Dashboard updates

#### Option 2: Start Watchdog (Auto-restart on crash)

```bash
python src/watchdog.py AI_Employee_Vault
```

This starts all processes and monitors their health, auto-restarting if they crash.

#### Option 3: Run Once (Testing)

```bash
python src/orchestrator.py AI_Employee_Vault --once
```

### Using the File System Watcher

1. **Drop a file** into the drop folder:
   ```
   AI_Employee_Vault/Inbox/Drop/your_file.pdf
   ```

2. **Watcher detects** the file and creates:
   - Copy in `AI_Employee_Vault/Inbox/`
   - Action file in `AI_Employee_Vault/Needs_Action/`

3. **Orchestrator processes** the action file and creates a plan

4. **Claude Code** can be invoked to process the plan:
   ```bash
   claude --cwd AI_Employee_Vault
   # Then prompt: "Process all files in /Needs_Action"
   ```

5. **Human approves** any sensitive actions by moving files from `Pending_Approval` to `Approved`

6. **Orchestrator executes** approved actions and moves to `Done`

### Dashboard

Open `AI_Employee_Vault/Dashboard.md` in Obsidian to see:
- Current system status
- Pending actions count
- Recent activity
- Process health

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Development mode (prevents real actions)
DRY_RUN=false

# Vault path
VAULT_PATH=/path/to/AI_Employee_Vault

# Logging
LOG_LEVEL=INFO
```

### Company Handbook

Edit `AI_Employee_Vault/Company_Handbook.md` to customize:
- Communication guidelines
- Payment thresholds
- Task prioritization rules
- Contact management

### Business Goals

Edit `AI_Employee_Vault/Business_Goals.md` to set:
- Revenue targets
- Key metrics
- Active projects
- Weekly goals

---

## Security

### Credential Management

**NEVER** store credentials in the Obsidian vault or `.env` file for production use.

- Use environment variables for API keys
- Use system keychain for sensitive data (banking, WhatsApp sessions)
- Rotate credentials monthly

### Human-in-the-Loop

The AI Employee **always** requires human approval for:
- Payments to new recipients
- Payments over $100 (configurable in Company_Handbook.md)
- Emails to unknown contacts
- Bulk communications
- Any irreversible action

### Audit Logging

All actions are logged to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` in this format:

```json
{
  "timestamp": "2026-03-18T10:30:00",
  "action_type": "file_drop_processed",
  "actor": "filesystem_watcher",
  "target": "document.pdf",
  "result": "success"
}
```

---

## Troubleshooting

### Watcher not detecting files

1. Check that the drop folder exists: `AI_Employee_Vault/Inbox/Drop/`
2. Verify file permissions allow reading
3. Check logs: `AI_Employee_Vault/Logs/watcher_filesystem_watcher_YYYY-MM-DD.log`

### Orchestrator not processing files

1. Ensure orchestrator is running
2. Check that files have `.md` extension in `Needs_Action/`
3. Review orchestrator logs

### Python not found

On Windows, ensure Python is in your PATH or use:
```bash
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src/orchestrator.py AI_Employee_Vault
```

### Module not found errors

Reinstall dependencies:
```bash
pip install -r requirements.txt --upgrade
```

---

## Upgrading to Silver Tier

To add Silver Tier features:

1. **Gmail Watcher**: Implement `gmail_watcher.py` using Google API
2. **WhatsApp Watcher**: Implement using Playwright for WhatsApp Web
3. **MCP Server**: Set up email MCP for sending emails
4. **Approval Workflow**: Enhance the approval file format
5. **Scheduling**: Add cron jobs or Task Scheduler integration

---

## Hackathon Submission

### Tier Declaration
**Bronze Tier** - Foundation (Minimum Viable Deliverable)

### Features Implemented
- Obsidian vault with Dashboard, Company Handbook, Business Goals
- File System Watcher for local file drops
- Orchestrator for coordination
- Watchdog for health monitoring
- Audit logging
- Human-in-the-loop approval workflow

### Security Disclosure
- Credentials stored in environment variables (not in vault)
- Dry run mode available for testing
- All actions logged to audit trail
- HITL required for sensitive actions

### Demo Instructions
1. Start the orchestrator: `python src/orchestrator.py AI_Employee_Vault`
2. Drop a file into `AI_Employee_Vault/Inbox/Drop/`
3. Watch the action file appear in `Needs_Action/`
4. Review the Dashboard.md in Obsidian
5. Check audit logs in `Logs/`

---

## Learning Resources

- [Claude Code Fundamentals](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [Claude Code + Obsidian Integration](https://www.youtube.com/watch?v=sCIS05Qt79Y)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Model Context Protocol](https://modelcontextprotocol.io/introduction)

---

## License

This project is part of the Personal AI Employee Hackathon 0.

---

*Built with ❤️ for the Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026*
