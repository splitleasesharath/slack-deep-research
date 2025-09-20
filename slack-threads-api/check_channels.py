#!/usr/bin/env python3
"""
Check available channels and bot permissions
"""

import sys
import logging

# Fix Unicode output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_channels():
    """Check which channels the bot has access to"""
    client = WebClient(token=Config.SLACK_BOT_TOKEN)

    print("\n=== Checking Bot Permissions ===")

    try:
        auth_response = client.auth_test()
        print(f"✅ Bot authenticated as: {auth_response['user']}")
        print(f"   Team: {auth_response['team']}")
        print(f"   Bot ID: {auth_response['user_id']}")
    except SlackApiError as e:
        print(f"❌ Authentication failed: {e.response['error']}")
        return

    print("\n=== Checking Available Channels ===")

    try:
        response = client.conversations_list(
            types="public_channel,private_channel",
            exclude_archived=True,
            limit=100
        )

        channels = response.get('channels', [])
        print(f"Found {len(channels)} accessible channels:\n")

        for channel in channels:
            is_member = "✅" if channel.get('is_member') else "❌"
            channel_type = "Private" if channel.get('is_private') else "Public"
            print(f"{is_member} {channel['id']}: #{channel['name']} ({channel_type})")

            if channel['id'] == Config.SLACK_CHANNEL_ID:
                print(f"   ⭐ This is your configured channel")
                if not channel.get('is_member'):
                    print(f"   ⚠️ Bot is NOT a member - please add the bot to this channel!")

    except SlackApiError as e:
        print(f"❌ Error listing channels: {e.response['error']}")

    print("\n=== Checking Channel History Access ===")

    if Config.SLACK_CHANNEL_ID:
        try:
            response = client.conversations_history(
                channel=Config.SLACK_CHANNEL_ID,
                limit=1
            )
            print(f"✅ Can read history from configured channel {Config.SLACK_CHANNEL_ID}")
        except SlackApiError as e:
            error = e.response['error']
            if error == 'channel_not_found':
                print(f"❌ Channel {Config.SLACK_CHANNEL_ID} not found or bot doesn't have access")
                print("   Solution: Add the bot to the channel in Slack")
            elif error == 'missing_scope':
                print(f"❌ Missing required scope for reading history")
                print("   Solution: Add 'channels:history' scope and reinstall app")
            else:
                print(f"❌ Cannot read history: {error}")

    print("\n=== Required OAuth Scopes ===")
    print("Ensure your bot has these scopes:")
    print("  ✓ channels:read - List channels")
    print("  ✓ channels:history - Read channel messages")
    print("  ✓ chat:write - Send messages")
    print("  ✓ users:read - Get user info")
    print("  ✓ files:write - Upload files (optional)")
    print("  ✓ files:read - Read file info (optional)")


if __name__ == "__main__":
    check_channels()