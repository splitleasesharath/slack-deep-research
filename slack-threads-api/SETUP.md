# Slack Threads API - Setup Guide

This guide provides detailed step-by-step instructions for setting up the Slack Threads API on your system.

## Prerequisites

- Python 3.7 or higher installed
- Administrator access to a Slack workspace
- Git (for cloning the repository)

## Step 1: Create a Slack App

### 1.1 Navigate to Slack API
1. Open https://api.slack.com/apps in your browser
2. Sign in with your Slack workspace credentials

### 1.2 Create New App
1. Click **"Create New App"**
2. Choose **"From scratch"**
3. Enter your app name (e.g., "Thread Bot", "Message Automator")
4. Select your Slack workspace
5. Click **"Create App"**

## Step 2: Configure OAuth Permissions

### 2.1 Navigate to OAuth & Permissions
1. In the left sidebar, click **"OAuth & Permissions"**

### 2.2 Add Bot Token Scopes
1. Scroll to **"Scopes"** section
2. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
3. Add these required scopes one by one:
   - `chat:write` - Post messages in channels & conversations (REQUIRED)
   - `chat:write.public` - Post messages to channels without joining
   - `channels:read` - View basic information about public channels
   - `groups:read` - View basic information about private channels
   - `files:write` - Upload files and images (REQUIRED for image support)
   - `files:read` - View files shared in channels (REQUIRED for files_upload_v2)
   - `users:read` - View people in a workspace (optional, for user info)

   **Note**: For image uploads, you MUST have both `files:write` AND `files:read` scopes

### 2.3 Install App to Workspace
1. Scroll back to the top of the OAuth page
2. Click **"Install to Workspace"**
3. Review the permissions
4. Click **"Allow"**

### 2.4 Copy Credentials
After installation, you'll see your credentials:
1. **Bot User OAuth Token**: Copy this (starts with `xoxb-`)
2. Go to **"Basic Information"** in the sidebar
3. Under **"App Credentials"**, find and copy the **"Signing Secret"**

## Step 3: Get Channel ID

### 3.1 Find Your Channel ID
In Slack:
1. Open the channel you want to use
2. Click the channel name at the top
3. In the popup, scroll to the bottom
4. Copy the **Channel ID** (starts with `C`)

Alternative method:
1. Right-click on the channel name in the sidebar
2. Select **"View channel details"**
3. Copy the Channel ID at the bottom

## Step 4: Set Up the Project

### 4.1 Clone the Repository
```bash
git clone https://github.com/splitleasesharath/slack-threads-api.git
cd slack-threads-api
```

### 4.2 Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 4.4 Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` file with your credentials:
```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
SLACK_SIGNING_SECRET=YOUR-SIGNING-SECRET-HERE
SLACK_CHANNEL_ID=C1234567890  # Your channel ID

# Optional Configuration
DATABASE_URL=sqlite:///slack_messages.db
FLASK_SECRET_KEY=your-flask-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

## Step 5: Invite Bot to Channel

### 5.1 Add Bot to Channel
In your Slack channel:
1. Type `/invite @` and start typing your bot name
2. Select your bot from the dropdown
3. Press Enter

Alternative:
1. Type `/invite @your-bot-name` directly
2. Press Enter

## Step 6: Test the Setup

### 6.1 Run Authentication Test
```bash
python test_auth.py
```

Expected output:
```
Testing Slack Authentication...
==================================================
✅ Authentication successful!
   Bot Name: your-bot-name
   Team: Your Team Name
   Bot ID: UXXXXXXXXX

📍 Testing channel access...
   Channel ID: C1234567890
   ✅ Can access channel: #your-channel

📤 Testing message permissions...
   ✅ Can send messages!
   Message timestamp: 1758007411.676899
   ✅ Can create threads!
```

### 6.2 Run Usage Examples
```bash
python usage_example.py
```

This will send test messages to your channel demonstrating all features.

## Troubleshooting

### Issue: "missing_scope" Error

**Solution:**
1. Return to https://api.slack.com/apps
2. Select your app
3. Go to "OAuth & Permissions"
4. Add missing scopes under "Bot Token Scopes"
5. Click "Reinstall to Workspace"
6. Update your `.env` with the new token

### Issue: "channel_not_found" Error

**Solutions:**
1. Verify the channel ID is correct
2. Ensure bot is invited to the channel
3. For private channels, the bot must be a member

### Issue: "invalid_auth" Error

**Solutions:**
1. Check token starts with `xoxb-`
2. Verify token hasn't been revoked
3. Ensure no extra spaces in `.env` file
4. Try regenerating the token

### Issue: "not_in_channel" Error

**Solution:**
In the Slack channel, type:
```
/invite @your-bot-name
```

## Advanced Configuration

### Using Different Channels

You can override the default channel per message:
```python
client.send_message("Hello", channel="C_DIFFERENT_CHANNEL_ID")
```

### Multiple Workspaces

Create separate `.env` files:
```bash
.env.workspace1
.env.workspace2
```

Load specific config:
```python
from dotenv import load_dotenv
load_dotenv('.env.workspace1')
```

### Rate Limiting

Slack has rate limits. For batch operations:
```python
# Add delay between messages
client.send_batch_to_thread(
    thread_ts=thread_id,
    messages=messages,
    delay_seconds=1.0  # Adjust as needed
)
```

## Security Best Practices

1. **Never commit `.env` files** - Always use `.gitignore`
2. **Rotate tokens regularly** - Regenerate tokens periodically
3. **Use environment-specific configs** - Separate dev/prod credentials
4. **Limit scope permissions** - Only add scopes you actually need
5. **Monitor bot activity** - Review Slack audit logs regularly

## Next Steps

1. Review the [README.md](README.md) for usage examples
2. Check `usage_example.py` for code samples
3. Customize `slack_thread_client.py` for your needs
4. Build your automation workflows

## Getting Help

- Check [Slack API Documentation](https://api.slack.com)
- Review [Python Slack SDK Docs](https://slack.dev/python-slack-sdk/)
- Create an issue on [GitHub](https://github.com/splitleasesharath/slack-threads-api/issues)

---

Happy threading! 🚀