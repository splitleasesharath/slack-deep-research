#!/usr/bin/env python3
"""
Slack Message Retrieval Script
Retrieves messages from the past 24 hours and stores them in database.
Run this script periodically (e.g., via cron) to continuously collect messages.
"""

import argparse
import logging
from datetime import datetime, timedelta
from database_models import init_database, get_session, SlackMessage
from slack_message_retriever import SlackMessageRetriever
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Retrieve Slack messages and store in database')
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to look back (default: 24)'
    )
    parser.add_argument(
        '--channel',
        type=str,
        help='Channel ID to retrieve from (default: from config)'
    )
    parser.add_argument(
        '--include-bots',
        action='store_true',
        help='Include bot messages (default: user messages only)'
    )
    parser.add_argument(
        '--no-threads',
        action='store_true',
        help='Skip thread replies (default: include threads)'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database tables'
    )
    parser.add_argument(
        '--show-stats',
        action='store_true',
        help='Show retrieval statistics'
    )
    parser.add_argument(
        '--list-unprocessed',
        action='store_true',
        help='List unprocessed messages'
    )

    args = parser.parse_args()

    if args.init_db:
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        return

    retriever = SlackMessageRetriever()

    try:
        if args.show_stats:
            stats = retriever.get_retrieval_stats(days_back=7)
            print("\n=== Retrieval Statistics (Last 7 Days) ===")
            print(f"Total Retrievals: {stats['total_retrievals']}")
            print(f"Successful: {stats['successful_retrievals']}")
            print(f"Failed: {stats['failed_retrievals']}")
            print(f"Total Messages Retrieved: {stats['total_messages_retrieved']}")
            print(f"Unprocessed Messages: {stats['unprocessed_messages']}")

            print("\n=== Report Statistics ===")
            print(f"Messages Needing Reports: {stats['messages_needing_reports']}")
            print(f"Reports Generated: {stats['total_reports_generated']}")
            print(f"Reports Sent to Slack: {stats['total_reports_sent']}")
            print(f"Unsent Reports: {stats['unsent_reports']}")

            if stats['retrieval_logs']:
                print("\n=== Recent Retrieval Logs ===")
                for log in stats['retrieval_logs'][:5]:
                    print(f"  {log.retrieval_started_at}: Channel {log.channel_id} - "
                          f"New: {log.new_messages_added}, Skipped: {log.duplicate_messages_skipped}")
            return

        if args.list_unprocessed:
            unprocessed = retriever.get_unprocessed_messages(limit=20)
            print(f"\n=== Unprocessed Messages ({len(unprocessed)}) ===")
            for msg in unprocessed:
                print(f"  [{msg.sent_datetime}] @{msg.username}: {msg.text[:80]}...")
            return

        logger.info(f"Starting message retrieval for past {args.hours} hours")

        channel_id = args.channel or Config.SLACK_CHANNEL_ID
        if not channel_id:
            logger.error("No channel ID specified. Set SLACK_CHANNEL_ID in .env or use --channel")
            return

        user_only = not args.include_bots
        include_threads = not args.no_threads

        logger.info(f"Retrieving from channel: {channel_id}")
        logger.info(f"User messages only: {user_only}")
        logger.info(f"Include threads: {include_threads}")

        results = retriever.get_channel_messages(
            channel_id=channel_id,
            hours_back=args.hours,
            include_threads=include_threads,
            user_only=user_only
        )

        print("\n=== Retrieval Results ===")
        print(f"Total messages found: {results['total_messages_found']}")
        print(f"New messages added: {results['new_messages_added']}")
        print(f"Duplicates skipped: {results['duplicate_messages_skipped']}")
        print(f"Bot messages filtered: {results['bot_messages_filtered']}")

        if results['errors']:
            print(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")

        if results['new_messages_added'] > 0:
            session = get_session()
            recent = session.query(SlackMessage)\
                .order_by(SlackMessage.retrieved_at.desc())\
                .limit(5)\
                .all()

            print("\n=== Sample of Newly Retrieved Messages ===")
            for msg in recent:
                print(f"  [{msg.sent_datetime}] @{msg.username}: {msg.text[:80]}...")

            session.close()

    except Exception as e:
        logger.error(f"Error during retrieval: {str(e)}")
        raise

    finally:
        retriever.close()
        logger.info("Retrieval process completed")


if __name__ == "__main__":
    main()