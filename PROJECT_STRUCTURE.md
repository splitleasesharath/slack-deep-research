# Deep Research Orchestrator - Project Structure

## Overview
This project integrates Slack message retrieval with automated deep research generation using Google's Gemini AI. All required files are contained within this directory.

## Directory Structure

```
gemini-deep-research/
│
├── orchestrator.py                 # Main orchestrator script
├── orchestrator_concurrent.py      # Concurrent session support version
├── check_config.py                 # Configuration validator
├── run_orchestrator.bat           # Windows batch script to run orchestrator
├── run_orchestrator_concurrent.bat # Concurrent version batch script
├── requirements.txt                # Python dependencies
├── package.json                    # Root Node.js configuration
├── .gitignore                      # Git exclusions for sensitive data
├── ORCHESTRATOR_README.md          # Original documentation
├── PROJECT_STRUCTURE.md           # This file
│
├── slack-threads-api/              # Slack integration module
│   ├── slack_message_retriever.py # Message retrieval from Slack
│   ├── slack_thread_client.py     # Thread handling and sending
│   ├── database_models.py         # SQLAlchemy database models
│   ├── config.py                  # Configuration loader
│   ├── requirements.txt           # Python dependencies for module
│   ├── .env                       # Environment variables (NOT in Git)
│   └── slack_messages.db          # SQLite database (auto-created)
│
├── playwright-mcp-state/           # Browser automation for Gemini
│   ├── deep-research-with-start.js # Main research automation script
│   ├── package.json               # Node.js dependencies
│   ├── chrome-persistent-profile/  # Persistent Chrome session (NOT in Git)
│   └── deep-research-start-url.json # URL capture file (auto-created)
│
├── retrieve_report/                # Report retrieval module
│   ├── retrieve_report.js         # Report extraction script
│   ├── package.json               # Node.js dependencies
│   └── reports/                   # Generated reports directory (auto-created)
│
├── orchestrator_sessions/          # Session tracking (auto-created)
└── venv/                          # Python virtual environment (optional)
```

## Installation Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **Chrome**: Latest version
- **Windows**: For batch scripts (can be adapted for Linux/Mac)

### Python Dependencies
Install with: `pip install -r requirements.txt`
- slack-sdk==3.26.1
- python-dotenv==1.0.0
- SQLAlchemy==2.0.25
- schedule==1.2.0
- filelock==3.13.1

### Node.js Dependencies
Install with: `npm run install:all` (from root directory)

**playwright-mcp-state/**
- playwright@^1.40.0
- @modelcontextprotocol/sdk@^0.5.0

**retrieve_report/**
- playwright@^1.40.0

## Configuration Files Required

### 1. Slack API Configuration
Create `slack-threads-api/.env` with:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL_ID=C07RBxxxxxx
```

### 2. Chrome Session
The `playwright-mcp-state/chrome-persistent-profile/` directory maintains browser session:
- Auto-created on first run
- Contains cookies and authentication state
- Must manually login to Google/Gemini on first use
- Persists across runs

## External Dependencies

### Required Services
1. **Slack Workspace** with:
   - Bot with appropriate permissions (channels:history, chat:write, etc.)
   - Webhook configured for the target channel
   - Channel ID where messages are posted

2. **Google Account** for:
   - Access to Gemini Deep Research
   - One-time manual login required

### Database
- SQLite database (`slack_messages.db`) is auto-created
- No external database server required
- Schema managed by SQLAlchemy

## Running the Project

### First-Time Setup
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install Node dependencies: `npm run install:all`
3. Configure Slack tokens in `slack-threads-api/.env`
4. Run once manually to login to Gemini: `node playwright-mcp-state/deep-research-with-start.js`

### Normal Operation
Run the orchestrator: `run_orchestrator.bat` or `python orchestrator.py`

### Workflow
1. Retrieves new Slack messages
2. Processes oldest unprocessed message
3. Generates deep research via Gemini
4. Waits 9 minutes for report generation
5. Retrieves completed report
6. Sends report back to Slack thread
7. Retries up to 3 times with 5-minute delays if report not ready

## Important Notes

- All project files are self-contained in this directory
- No external file dependencies outside this folder
- Sensitive data (tokens, profiles, reports) are excluded from Git
- Chrome profile maintains session state across runs
- Database and reports are generated locally
- Supports concurrent sessions with file locking

## Troubleshooting

If files are missing:
1. Check `.gitignore` - some files are intentionally excluded
2. Run `npm run install:all` to install dependencies
3. `.env` file must be created manually with Slack tokens
4. Chrome profile directory is created on first run
5. Reports directory is created when first report is saved