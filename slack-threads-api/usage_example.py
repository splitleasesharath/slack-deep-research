from slack_thread_client import SlackThreadClient
import time

def main():
    # Initialize the client
    client = SlackThreadClient()

    print("Slack Thread API - Usage Examples\n")
    print("=" * 50)

    # Example 1: Send a simple message (not threaded)
    print("\n1. Sending a simple message...")
    response = client.send_message("Hello from Slack Thread API!")
    if response and response.get('ok'):
        print(f"   Message sent successfully!")
        print(f"   Message timestamp: {response['ts']}")

    # Example 2: Start a new thread and get thread_ts
    print("\n2. Starting a new thread...")
    thread_ts = client.start_thread("🚀 This is the start of a new thread!")
    if thread_ts:
        print(f"   Thread started successfully!")
        print(f"   Thread ID (save this): {thread_ts}")

        # Example 3: Reply to the thread using thread_ts
        print("\n3. Replying to the thread...")
        time.sleep(1)
        reply = client.reply_to_thread(
            thread_ts=thread_ts,
            text="This is the first reply in the thread"
        )
        if reply and reply.get('ok'):
            print(f"   Reply sent successfully!")

        # Example 4: Send multiple messages to the thread
        print("\n4. Sending batch messages to thread...")
        messages = [
            "📊 Processing data...",
            "✅ Step 1 completed",
            "✅ Step 2 completed",
            "🎉 All tasks finished!"
        ]
        responses = client.send_batch_to_thread(
            thread_ts=thread_ts,
            messages=messages,
            delay_seconds=0.5
        )
        print(f"   Sent {len(messages)} messages to thread")

    # Example 5: Create thread with rich formatting
    print("\n5. Creating thread with rich formatting...")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "System Status Update"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Status:* ✅ All systems operational\n*Uptime:* 99.9%\n*Last Check:* Just now"
            }
        }
    ]

    formatted_thread_ts = client.start_thread(
        initial_message="System Status",
        blocks=blocks
    )

    if formatted_thread_ts:
        print(f"   Rich formatted thread created!")
        print(f"   Thread ID: {formatted_thread_ts}")

    # Show active threads
    print("\n6. Active threads in this session:")
    active = client.get_active_threads()
    for ts, info in active.items():
        print(f"   - Thread {ts}: {info['initial_message']}")

    print("\n" + "=" * 50)
    print("Examples completed! Check your Slack channel.")

if __name__ == "__main__":
    main()