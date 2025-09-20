# Slack Message Retrieval Setup Guide

## Prerequisites

1. **Slack App with Required Permissions**
2. **Python 3.7+ installed**
3. **Database (SQLite by default, or PostgreSQL/MySQL)**

## Step 1: Configure Slack App Permissions

### Required OAuth Scopes

Go to [https://api.slack.com/apps](https://api.slack.com/apps) → Your App → OAuth & Permissions

Add these Bot Token Scopes:

For **PUBLIC** channels:
- `chat:write` - Send messages
- `channels:read` - List public channels
- `channels:history` - Read public channel history
- `users:read` - Get user information

For **PRIVATE** channels (groups):
- `chat:write` - Send messages
- `groups:read` - List private channels
- `groups:history` - Read private channel history (CRITICAL)
- `users:read` - Get user information

Optional scopes:
- `files:write` - Upload files
- `files:read` - Read file info

**IMPORTANT**: After adding scopes:
1. Click "Reinstall to Workspace"
2. Copy the NEW Bot User OAuth Token
3. Update your `.env` file

## Step 2: Add Bot to Channel

### In Slack:
1. Open the channel you want to retrieve messages from
2. Click channel name at the top
3. Click "Integrations" tab
4. Click "Add apps"
5. Search for your bot app name
6. Click "Add" to add the bot to the channel

### Alternative method:
In the channel, type: `/invite @YourBotName`

## Step 3: Find Your Channel ID

In Slack:
1. Click on the channel name
2. Scroll to the bottom
3. Copy the Channel ID (starts with C, like C09APJB9BK7)

## Step 4: Configure Environment

Create or update `.env` file:

```bash
SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
SLACK_CHANNEL_ID="C09APJB9BK7"
SLACK_SIGNING_SECRET="your-signing-secret"

# Database Configuration
DATABASE_URL=sqlite:///slack_messages.db
```

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Initialize Database

```bash
python retrieve_messages.py --init-db
```

## Step 7: Verify Setup

### Check Permissions:
```bash
python check_permissions.py
```

Expected output:
- ✅ chat:write
- ✅ channels:history
- ✅ users:read

### Check Channel Access:
```bash
python check_channels.py
```

Expected output:
- Bot should be member of your channel
- Should be able to read history

## Step 8: Test Message Retrieval

### Small test (1 hour):
```bash
python retrieve_messages.py --hours 1
```

### Full test (24 hours):
```bash
python retrieve_messages.py
```

## Troubleshooting

### Error: `channel_not_found`
**Solution**: Add the bot to the channel (Step 2)

### Error: `missing_scope`
**Solution**:
1. Add required scopes in Slack app settings
2. Reinstall app to workspace
3. Copy new token to `.env`

### Error: `invalid_auth`
**Solution**: Check your bot token in `.env` file

### No messages retrieved
**Possible causes**:
- No messages in the specified time period
- Bot was just added and can only see new messages
- Channel is private and bot needs invitation

## Schedule Automatic Retrieval

### Linux/Mac (crontab):
```bash
# Edit crontab
crontab -e

# Add line to run every hour
0 * * * * cd /path/to/slack-threads-api && python retrieve_messages.py
```

### Windows Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., hourly)
4. Action: Start program
5. Program: `python`
6. Arguments: `retrieve_messages.py`
7. Start in: `C:\path\to\slack-threads-api`

## Usage Examples

### Retrieve with options:
```bash
# Include bot messages
python retrieve_messages.py --include-bots

# Different time window
python retrieve_messages.py --hours 48

# Specific channel
python retrieve_messages.py --channel C1234567890
```

### View statistics:
```bash
python retrieve_messages.py --show-stats
```

### Process messages:
```bash
python process_messages.py
```

## Database Schema

Messages are stored with:
- `ts`: Message timestamp (primary key)
- `channel_id`: Channel where message was posted
- `user_id`: User who sent the message
- `username`: User's display name
- `text`: Message content
- `sent_datetime`: When message was sent
- `retrieved_at`: When we retrieved it
- `processed`: Whether message has been processed
- `is_bot`: Whether message is from a bot

## Next Steps

1. Customize `process_messages.py` for your use case
2. Set up periodic retrieval via cron/scheduler
3. Build analytics or integrations using the stored messages