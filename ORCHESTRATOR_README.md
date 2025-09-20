# Deep Research Orchestrator

## Overview

The Deep Research Orchestrator is an integrated automation system that combines Slack message monitoring, AI-powered deep research generation, and automated report delivery. It creates a complete workflow from receiving research requests in Slack to delivering comprehensive reports back to the channel.

## Workflow

The orchestrator follows this automated workflow:

1. **Message Retrieval**: Retrieves new messages from configured Slack channel
2. **Message Selection**: Identifies the oldest unprocessed message
3. **Research Generation**: Launches Gemini Deep Research with the message content
4. **URL Capture**: Captures the generated report URL
5. **Scheduled Retrieval**: Waits 20 minutes for report generation
6. **Report Extraction**: Retrieves the complete report content
7. **Slack Delivery**: Sends the report back to Slack as a reply or new message

## Quick Start

### One-Click Launch

Double-click `START_ORCHESTRATOR.bat` for immediate single-run execution with default settings.

### Interactive Launch

Run `run_orchestrator.bat` for an interactive menu with options:
- Single run mode (process one message)
- Continuous mode (30-minute intervals)
- Custom interval mode

### Command Line

```bash
# Single run (processes one message then waits for scheduled tasks)
python orchestrator.py

# Continuous mode with 30-minute intervals
python orchestrator.py --continuous

# Continuous mode with custom interval (e.g., 60 minutes)
python orchestrator.py --continuous 60
```

## Configuration

### Prerequisites

1. **Slack Bot Setup**
   - Create a Slack app with required OAuth scopes
   - Copy `.env.example` to `.env` in `slack-threads-api` folder
   - Update with your Slack bot token and channel ID

2. **Chrome Session**
   - Ensure you're logged into Gemini in the persistent Chrome profile
   - Located at `playwright-mcp-state/chrome-persistent-profile`

### Configuration Check

Run `python check_config.py` to verify all components are properly configured.

## Components

### orchestrator.py
Main orchestration script that coordinates the entire workflow.

### slack-threads-api/
Python module for Slack integration with SQLite database for message tracking.

### playwright-mcp-state/
Playwright scripts for automating Gemini Deep Research.

### retrieve_report/
Node.js module for extracting completed reports from Gemini.

## Database

Messages are tracked through these stages in SQLite database:
- `processed`: Whether the message has been processed
- `report_generated`: Whether a report was generated
- `report_sent_to_slack`: Whether the report was sent to Slack

## Logging

All operations are logged to:
- Console output (real-time monitoring)
- `orchestrator.log` file (persistent log)

## Scheduling

The orchestrator uses a 20-minute delay between research initiation and report retrieval, allowing time for Gemini to generate comprehensive reports.

## Error Handling

- Failed research attempts mark messages as processed to avoid loops
- Database transactions are atomic with rollback on errors
- Timeout protection for all external processes
- Graceful handling of missing reports

## Files Created

- `orchestrator.log`: Detailed execution log
- `slack-threads-api/slack_messages.db`: Message database
- `retrieve_report/reports/`: Saved report files
- `playwright-mcp-state/deep-research-dynamic.js`: Dynamically generated script

## Troubleshooting

1. **"Python not found"**: Install Python 3.7+ and add to PATH
2. **"Node.js not found"**: Install Node.js and add to PATH
3. **"Missing .env file"**: Copy `.env.example` to `.env` and configure
4. **"Chrome session error"**: Log into Gemini using the persistent Chrome profile
5. **"No unprocessed messages"**: All messages have been processed; new messages will be processed when received

## Manual Testing

To test individual components:

```bash
# Test Slack message retrieval
cd slack-threads-api
python retrieve_messages.py --hours 24

# Test deep research generation
cd playwright-mcp-state
node deep-research-with-start.js

# Test report retrieval
cd retrieve_report
node retrieve_report.js <URL>
```

## Support

Check logs in `orchestrator.log` for detailed error messages and workflow status.