# Slack Threads API

A lightweight Python client for sending messages to Slack with full threading support using the Slack Web API. Perfect for automation, notifications, and building conversation threads programmatically.

## Features

### Messaging & Threading
- Send simple messages to Slack channels
- Create and manage message threads
- Reply to existing threads using thread timestamps
- Send batch messages to threads
- Rich formatting with blocks and attachments
- Thread ID tracking for continuous conversations
- Image and file uploads with thread support

### Message Retrieval & Storage (NEW)
- Retrieve messages from channels for any time period
- Store messages in database with automatic duplicate detection
- Track message retrieval and processing status
- Filter to user-only messages (exclude bots)
- Retrieve thread replies automatically
- Support for SQLite, PostgreSQL, and MySQL databases

## Installation

1. Clone the repository:
```bash
git clone https://github.com/splitleasesharath/slack-threads-api.git
cd slack-threads-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Slack credentials:
   - Copy `.env.example` to `.env`
   - Update the values with your Slack app credentials:
     - `SLACK_BOT_TOKEN`: Your Slack bot token (starts with xoxb-)
     - `SLACK_SIGNING_SECRET`: Your Slack app signing secret
     - `SLACK_CHANNEL_ID`: Default channel ID for messages

## Slack App Setup

1. Create a Slack app at https://api.slack.com/apps
2. Add OAuth Scopes:
   - `chat:write` - Send messages (REQUIRED)
   - `chat:write.public` - Send messages to public channels
   - `channels:read` - View basic channel info (for public channels)
   - `channels:history` - Read public channel history
   - `groups:read` - View basic info for private channels (REQUIRED for private)
   - `groups:history` - Read private channel history (REQUIRED for private)
   - `users:read` - View user info (REQUIRED for username retrieval)
   - `files:write` - Upload files and images (REQUIRED for image support)
   - `files:read` - Read file information (REQUIRED for image uploads with files_upload_v2)

**⚠️ IMPORTANT**: After adding new scopes, you MUST:
- Click "Reinstall to Workspace"
- Copy the NEW Bot User OAuth Token (it changes!)
- Update your .env with the new token

3. Install the app to your workspace
4. Copy the Bot User OAuth Token

## Usage

### Basic Usage

```python
from slack_thread_client import SlackThreadClient

# Initialize client
client = SlackThreadClient()

# Send a simple message
response = client.send_message("Hello, Slack!")

# Start a new thread and get thread_ts
thread_ts = client.start_thread("Starting a new conversation thread")

# Reply to the thread using thread_ts
client.reply_to_thread(
    thread_ts=thread_ts,
    text="This is a reply in the thread"
)

# Send multiple messages to a thread
messages = ["Step 1 complete", "Step 2 complete", "All done!"]
client.send_batch_to_thread(
    thread_ts=thread_ts,
    messages=messages
)
```

### Advanced Usage with Formatting

```python
# Create thread with rich formatting
blocks = [
    {
        "type": "header",
        "text": {"type": "plain_text", "text": "Status Update"}
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Status:* ✅ Operational\n*Time:* Now"
        }
    }
]

thread_ts = client.start_thread(
    initial_message="System Status",
    blocks=blocks
)
```

### Image Upload Usage

**Important**: Image uploads require both `files:write` AND `files:read` scopes in your Slack app configuration.

```python
# Upload image to main channel
response = client.upload_file(
    file_path="image.png",
    initial_comment="Here's the screenshot",
    title="Screenshot"
)

# Upload image to thread
thread_ts = client.start_thread("Bug report with images")
client.upload_file(
    file_path="error_screenshot.png",
    thread_ts=thread_ts,
    initial_comment="Error screenshot attached",
    title="Error Screenshot"
)

# Upload from bytes (e.g., generated image)
image_bytes = generate_chart()  # Your image generation code
client.upload_file(
    file_content=image_bytes,
    filename="chart.png",
    thread_ts=thread_ts,
    initial_comment="Generated chart"
)
```

### Run Examples

```bash
python usage_example.py              # Basic usage examples
python test_thread_only.py          # Test thread functionality (text only)
python test_image_upload.py         # Test image upload (requires files:read scope)
python check_permissions.py         # Check your token's permissions
```

## API Reference

### SlackThreadClient

#### `send_message(text, channel=None, thread_ts=None, blocks=None, attachments=None)`
Send a message to Slack. Returns response with `thread_ts` for threading.

#### `start_thread(initial_message, channel=None, blocks=None)`
Start a new thread and return the thread timestamp.

#### `reply_to_thread(thread_ts, text, channel=None, blocks=None)`
Reply to an existing thread using its timestamp.

#### `send_batch_to_thread(thread_ts, messages, channel=None, delay_seconds=0.5)`
Send multiple messages to a thread with optional delay.

#### `get_thread_replies(channel, thread_ts, limit=100)`
Retrieve all messages in a thread.

#### `get_active_threads()`
Get all active thread IDs stored in the current session.

#### `upload_file(file_path=None, file_content=None, filename=None, channel=None, thread_ts=None, initial_comment=None, title=None)`
Upload a file or image to Slack. Supports both file paths and bytes content. Use `thread_ts` to upload to a thread.

## Thread Management

When you start a thread, save the returned `thread_ts` value. This is your thread identifier that you'll use for all future replies to that thread:

```python
# Start a conversation
thread_ts = client.start_thread("Customer inquiry #1234")
print(f"Thread ID: {thread_ts}")  # Save this ID

# Later, reply to the same thread
client.reply_to_thread(thread_ts, "Following up on this inquiry...")
```

## Verified Features & Test Results

✅ **Fully Working:**
- Send messages to main channel
- Create new threads
- Reply to existing threads using thread_ts
- Send batch messages to threads with delays
- Track active threads in session
- Rich formatting with Slack blocks

⚠️ **Image Uploads:**
- Requires both `files:write` AND `files:read` OAuth scopes
- The Slack SDK's `files_upload_v2` method needs `files:read` to fetch file info
- Alternative: Use older `files_upload` method (deprecated but doesn't need files:read)

## Message Retrieval & Database Storage

### Initialize Database

```bash
python retrieve_messages.py --init-db
```

### Retrieve Messages

Retrieve messages from the past 24 hours (default):
```bash
python retrieve_messages.py
```

Retrieve messages from specific time period:
```bash
python retrieve_messages.py --hours 48
```

Retrieve from specific channel:
```bash
python retrieve_messages.py --channel C1234567890
```

Include bot messages:
```bash
python retrieve_messages.py --include-bots
```

### View Statistics

```bash
python retrieve_messages.py --show-stats
```

### Process Messages

```bash
python process_messages.py
```

### Schedule Periodic Retrieval

For Linux/Mac (crontab):
```bash
# Run every hour
0 * * * * cd /path/to/slack-threads-api && python retrieve_messages.py

# Run every 30 minutes
*/30 * * * * cd /path/to/slack-threads-api && python retrieve_messages.py --hours 1
```

For Windows (Task Scheduler):
Create a scheduled task to run `retrieve_messages.py` periodically.

## Environment Variables

Create a `.env` file with:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CHANNEL_ID=C1234567890

# Database Configuration (SQLite default)
DATABASE_URL=sqlite:///slack_messages.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/slack_messages
# For MySQL:
# DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/slack_messages
```

## Requirements

- Python 3.7+
- slack-sdk 3.26.1
- python-dotenv 1.0.0
- Pillow 10.2.0 (optional, for image testing)

## License

MIT