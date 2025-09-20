import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import Config

def check_token_permissions():
    """Check and display all permissions for the current token"""
    client = WebClient(token=Config.SLACK_BOT_TOKEN)

    print("Checking Slack Token Permissions")
    print("=" * 50)
    print(f"Token: {Config.SLACK_BOT_TOKEN[:20]}...")
    print()

    try:
        # Get auth info
        auth_response = client.auth_test()
        print(f"✅ Authentication successful!")
        print(f"   Bot: {auth_response.get('user', 'Unknown')}")
        print(f"   Team: {auth_response.get('team', 'Unknown')}")
        print(f"   User ID: {auth_response.get('user_id', 'Unknown')}")
        print()

        # Try to get OAuth scopes
        print("📋 OAuth Scopes Available:")

        # Method 1: From auth.test response
        if 'scopes' in auth_response:
            scopes = auth_response['scopes']
            if scopes:
                for scope in scopes.split(','):
                    print(f"   - {scope}")
            else:
                print("   No scopes found in auth.test")

        # Method 2: Try to send a test message to check chat:write
        print("\n🔍 Testing Specific Permissions:")

        # Test chat:write
        try:
            test_msg = client.chat_postMessage(
                channel=Config.SLACK_CHANNEL_ID,
                text="Permission test: chat:write"
            )
            print("   ✅ chat:write - Can send messages")

            # Delete test message
            client.chat_delete(
                channel=Config.SLACK_CHANNEL_ID,
                ts=test_msg['ts']
            )
        except SlackApiError as e:
            if 'missing_scope' in str(e):
                print(f"   ❌ chat:write - NOT available")
                print(f"      Error: {e.response.get('error', 'Unknown')}")
                if 'needed' in e.response:
                    print(f"      Needed: {e.response['needed']}")
                if 'provided' in e.response:
                    print(f"      Current scopes: {e.response['provided']}")
            else:
                print(f"   ⚠️  chat:write - Error: {e.response.get('error', 'Unknown')}")

        # Test files:write
        print("\n   Testing files:write...")
        try:
            # Try to get upload URL (minimal test for files:write)
            test_upload = client.files_getUploadURLExternal(
                filename="test.txt",
                length=10
            )
            print("   ✅ files:write - Can upload files")
        except SlackApiError as e:
            if 'missing_scope' in str(e):
                print(f"   ❌ files:write - NOT available")
                if 'provided' in e.response:
                    print(f"      Current scopes: {e.response['provided']}")
            else:
                print(f"   ⚠️  files:write - Error: {e.response.get('error', 'Unknown')}")

        # Test channels:read
        try:
            client.conversations_info(channel=Config.SLACK_CHANNEL_ID)
            print("   ✅ channels:read - Can read channel info")
        except:
            print("   ❌ channels:read - NOT available")

        # Test channels:history / groups:history
        try:
            client.conversations_history(channel=Config.SLACK_CHANNEL_ID, limit=1)
            print("   ✅ channels:history/groups:history - Can read message history")
        except SlackApiError as e:
            if 'missing_scope' in str(e):
                error_msg = f"   ❌ history access - NOT available"
                if 'needed' in e.response:
                    needed = e.response['needed']
                    error_msg += f"\n      Need scope: {needed}"
                    if needed == 'groups:history':
                        error_msg += "\n      This is a PRIVATE channel - add 'groups:history' scope"
                print(error_msg)
            elif 'channel_not_found' in str(e):
                print(f"   ❌ history access - Channel not found or bot not in channel")
            else:
                print(f"   ⚠️  history access - Error: {e.response.get('error', 'Unknown')}")

        # Test users:read
        try:
            client.users_info(user=auth_response.get('user_id'))
            print("   ✅ users:read - Can read user info")
        except:
            print("   ❌ users:read - NOT available")

    except SlackApiError as e:
        print(f"❌ Authentication failed: {e.response['error']}")
        print("\nPossible issues:")
        print("1. Token is invalid or expired")
        print("2. Token doesn't have required scopes")
        print("3. App needs to be reinstalled after adding scopes")

    print("\n" + "=" * 50)
    print("\n📝 Next Steps:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Select your app")
    print("3. Go to 'OAuth & Permissions'")
    print("4. Check 'Bot Token Scopes' section")
    print("5. Ensure these scopes are added:")
    print("   - chat:write")
    print("   - channels:read")
    print("   - channels:history")
    print("   - users:read")
    print("   - files:write (optional)")
    print("   - files:read (optional)")
    print("6. Click 'Reinstall to Workspace' if you added new scopes")
    print("7. Copy the new Bot User OAuth Token")
    print("8. Update your .env file with the new token")

if __name__ == "__main__":
    check_token_permissions()