#!/usr/bin/env python3
"""
Message Processing Script
Example script showing how to process retrieved messages
"""

import logging
from datetime import datetime
from database_models import get_session, SlackMessage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessageProcessor:
    def __init__(self):
        self.session = get_session()

    def process_batch(self, batch_size: int = 50):
        """
        Process a batch of unprocessed messages
        """
        unprocessed = self.session.query(SlackMessage)\
            .filter_by(processed=False)\
            .order_by(SlackMessage.sent_datetime)\
            .limit(batch_size)\
            .all()

        logger.info(f"Found {len(unprocessed)} unprocessed messages")

        for message in unprocessed:
            try:
                self.process_message(message)

                message.processed = True
                message.processed_at = datetime.utcnow()
                self.session.commit()

                logger.info(f"Processed message: {message.ts}")

            except Exception as e:
                logger.error(f"Error processing message {message.ts}: {str(e)}")
                self.session.rollback()

    def process_message(self, message: SlackMessage):
        """
        Process a single message
        Add your custom processing logic here
        """
        logger.info(f"Processing message from @{message.username}: {message.text[:50]}...")

        if message.text and 'urgent' in message.text.lower():
            logger.warning(f"URGENT message detected from {message.username}")

        if message.attachments:
            logger.info(f"Message has {len(message.attachments)} attachments")

        if message.files:
            logger.info(f"Message has {len(message.files)} files")

        if message.thread_ts and message.thread_ts != message.ts:
            logger.info(f"This is a thread reply to {message.thread_ts}")

        if message.reply_count > 0:
            logger.info(f"This message has {message.reply_count} replies")

    def get_statistics(self):
        """
        Get processing statistics
        """
        total = self.session.query(SlackMessage).count()
        processed = self.session.query(SlackMessage).filter_by(processed=True).count()
        unprocessed = self.session.query(SlackMessage).filter_by(processed=False).count()

        user_messages = self.session.query(SlackMessage).filter_by(is_bot=False).count()
        bot_messages = self.session.query(SlackMessage).filter_by(is_bot=True).count()

        threads = self.session.query(SlackMessage)\
            .filter(SlackMessage.thread_ts == SlackMessage.ts)\
            .filter(SlackMessage.reply_count > 0)\
            .count()

        return {
            'total_messages': total,
            'processed': processed,
            'unprocessed': unprocessed,
            'user_messages': user_messages,
            'bot_messages': bot_messages,
            'threads': threads
        }

    def close(self):
        self.session.close()


def main():
    processor = MessageProcessor()

    try:
        stats = processor.get_statistics()
        print("\n=== Message Statistics ===")
        print(f"Total Messages: {stats['total_messages']}")
        print(f"Processed: {stats['processed']}")
        print(f"Unprocessed: {stats['unprocessed']}")
        print(f"User Messages: {stats['user_messages']}")
        print(f"Bot Messages: {stats['bot_messages']}")
        print(f"Threads: {stats['threads']}")

        if stats['unprocessed'] > 0:
            print(f"\nProcessing {min(50, stats['unprocessed'])} messages...")
            processor.process_batch(batch_size=50)
            print("Processing complete")

    finally:
        processor.close()


if __name__ == "__main__":
    main()