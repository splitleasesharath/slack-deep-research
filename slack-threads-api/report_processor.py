#!/usr/bin/env python3
"""
Report Generation and Sending Script
Demonstrates the report workflow using the new tracking fields
"""

import logging
from datetime import datetime
from slack_message_retriever import SlackMessageRetriever
from slack_thread_client import SlackThreadClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportProcessor:
    def __init__(self):
        self.retriever = SlackMessageRetriever()
        self.slack_client = SlackThreadClient()

    def generate_report(self, message):
        """
        Generate a report for a message
        This is where you would implement your custom report generation logic
        """
        report_content = f"""
=== REPORT ===
Message: {message.text[:100]}...
User: {message.username}
Sent: {message.sent_datetime}
Channel: {message.channel_id}

[Your custom report logic would go here]
Generated at: {datetime.utcnow()}
===============
"""
        return report_content

    def process_messages_needing_reports(self, limit=5):
        """
        Process messages that need reports generated
        """
        messages = self.retriever.get_messages_needing_reports(limit=limit)

        if not messages:
            logger.info("No messages need reports")
            return 0

        logger.info(f"Found {len(messages)} messages needing reports")

        for message in messages:
            try:
                # Generate the report
                report_content = self.generate_report(message)

                # Mark report as generated
                self.retriever.mark_report_generated(
                    ts=message.ts,
                    report_content=report_content
                )

                logger.info(f"Report generated for message {message.ts} from @{message.username}")

            except Exception as e:
                logger.error(f"Error generating report for {message.ts}: {e}")

        return len(messages)

    def send_unsent_reports_to_slack(self, limit=5):
        """
        Send reports that have been generated but not sent to Slack
        """
        messages = self.retriever.get_messages_with_unsent_reports(limit=limit)

        if not messages:
            logger.info("No unsent reports")
            return 0

        logger.info(f"Found {len(messages)} unsent reports")

        for message in messages:
            try:
                # Send report to Slack (as a reply to original message if it's in a thread)
                if message.thread_ts:
                    # Reply to the existing thread
                    response = self.slack_client.reply_to_thread(
                        thread_ts=message.thread_ts,
                        text=f"Report for message from @{message.username}:\n{message.report_content}"
                    )
                else:
                    # Create a new thread with the report
                    response = self.slack_client.send_message(
                        text=f"Report for message from @{message.username}:\n{message.report_content}",
                        channel=message.channel_id
                    )

                if response and response.get('ok'):
                    # Mark report as sent
                    thread_ts = response.get('thread_ts') or response.get('ts')
                    self.retriever.mark_report_sent_to_slack(
                        ts=message.ts,
                        thread_ts=thread_ts
                    )
                    logger.info(f"Report sent to Slack for message {message.ts}")

            except Exception as e:
                logger.error(f"Error sending report for {message.ts}: {e}")

        return len(messages)

    def get_report_statistics(self):
        """
        Get statistics about reports
        """
        stats = self.retriever.get_retrieval_stats(days_back=30)

        return {
            'messages_needing_reports': stats['messages_needing_reports'],
            'total_reports_generated': stats['total_reports_generated'],
            'total_reports_sent': stats['total_reports_sent'],
            'unsent_reports': stats['unsent_reports']
        }

    def close(self):
        self.retriever.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Process reports for Slack messages')
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate reports for processed messages'
    )
    parser.add_argument(
        '--send',
        action='store_true',
        help='Send unsent reports to Slack'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show report statistics'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Number of messages to process (default: 5)'
    )

    args = parser.parse_args()

    processor = ReportProcessor()

    try:
        if args.stats:
            stats = processor.get_report_statistics()
            print("\n=== Report Statistics ===")
            print(f"Messages Needing Reports: {stats['messages_needing_reports']}")
            print(f"Total Reports Generated: {stats['total_reports_generated']}")
            print(f"Total Reports Sent: {stats['total_reports_sent']}")
            print(f"Unsent Reports: {stats['unsent_reports']}")

        elif args.generate:
            count = processor.process_messages_needing_reports(limit=args.limit)
            print(f"Generated {count} reports")

        elif args.send:
            count = processor.send_unsent_reports_to_slack(limit=args.limit)
            print(f"Sent {count} reports to Slack")

        else:
            # Default: show stats
            stats = processor.get_report_statistics()
            print("\n=== Report Pipeline Status ===")
            print(f"Messages Needing Reports: {stats['messages_needing_reports']}")
            print(f"Unsent Reports: {stats['unsent_reports']}")

            if stats['messages_needing_reports'] > 0:
                print("\nRun with --generate to create reports")
            if stats['unsent_reports'] > 0:
                print("Run with --send to send reports to Slack")

    finally:
        processor.close()


if __name__ == "__main__":
    main()