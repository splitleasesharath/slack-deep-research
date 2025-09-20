import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session
from config import Config
from database_models import SlackMessage, MessageRetrievalLog, get_session, init_database
from slack_thread_client import SlackThreadClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackMessageRetriever(SlackThreadClient):
    def __init__(self, token: str = None):
        super().__init__(token)
        self.db_session = get_session()

    def get_channel_messages(
        self,
        channel_id: str = None,
        hours_back: int = 24,
        include_threads: bool = True,
        user_only: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve messages from a channel for the past N hours

        Args:
            channel_id: Channel ID (defaults to configured channel)
            hours_back: How many hours back to retrieve (default 24)
            include_threads: Whether to include thread replies
            user_only: Filter to only user messages (exclude bots)

        Returns:
            Dictionary with retrieval statistics
        """
        channel_id = channel_id or self.default_channel

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        oldest_timestamp = start_time.timestamp()
        latest_timestamp = end_time.timestamp()

        retrieval_log = MessageRetrievalLog(
            retrieval_started_at=datetime.utcnow(),
            channel_id=channel_id,
            start_time=start_time,
            end_time=end_time,
            status='in_progress'
        )
        self.db_session.add(retrieval_log)
        self.db_session.commit()

        stats = {
            'total_messages_found': 0,
            'new_messages_added': 0,
            'duplicate_messages_skipped': 0,
            'bot_messages_filtered': 0,
            'errors': []
        }

        try:
            logger.info(f"Retrieving messages from channel {channel_id} for past {hours_back} hours")

            messages = self._fetch_channel_history(
                channel_id,
                oldest_timestamp,
                latest_timestamp
            )

            stats['total_messages_found'] = len(messages)
            logger.info(f"Found {len(messages)} messages in channel history")

            for message in messages:
                if user_only and self._is_bot_message(message):
                    stats['bot_messages_filtered'] += 1
                    continue

                if self._message_exists(message['ts']):
                    stats['duplicate_messages_skipped'] += 1
                    continue

                self._store_message(message, channel_id)
                stats['new_messages_added'] += 1

                if include_threads and message.get('thread_ts') == message.get('ts'):
                    thread_messages = self._fetch_thread_replies(channel_id, message['ts'])
                    for thread_msg in thread_messages[1:]:
                        if user_only and self._is_bot_message(thread_msg):
                            stats['bot_messages_filtered'] += 1
                            continue

                        if self._message_exists(thread_msg['ts']):
                            stats['duplicate_messages_skipped'] += 1
                            continue

                        self._store_message(thread_msg, channel_id)
                        stats['new_messages_added'] += 1

            self.db_session.commit()

            retrieval_log.retrieval_completed_at = datetime.utcnow()
            retrieval_log.total_messages_found = stats['total_messages_found']
            retrieval_log.new_messages_added = stats['new_messages_added']
            retrieval_log.duplicate_messages_skipped = stats['duplicate_messages_skipped']
            retrieval_log.bot_messages_filtered = stats['bot_messages_filtered']
            retrieval_log.status = 'completed'
            self.db_session.commit()

            logger.info(f"Retrieval completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during message retrieval: {str(e)}")
            retrieval_log.status = 'failed'
            retrieval_log.error_message = str(e)
            self.db_session.commit()
            stats['errors'].append(str(e))
            return stats

    def _fetch_channel_history(
        self,
        channel_id: str,
        oldest: float,
        latest: float
    ) -> List[Dict]:
        """
        Fetch channel history using pagination
        """
        all_messages = []
        cursor = None

        try:
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(oldest),
                    latest=str(latest),
                    limit=200,
                    cursor=cursor
                )

                messages = response.get('messages', [])
                all_messages.extend(messages)

                if not response.get('has_more', False):
                    break

                cursor = response.get('response_metadata', {}).get('next_cursor')

            return all_messages

        except SlackApiError as e:
            logger.error(f"Error fetching channel history: {e.response['error']}")
            raise

    def _fetch_thread_replies(
        self,
        channel_id: str,
        thread_ts: str
    ) -> List[Dict]:
        """
        Fetch all replies in a thread
        """
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=1000
            )
            return response.get('messages', [])

        except SlackApiError as e:
            logger.error(f"Error fetching thread replies: {e.response['error']}")
            return []

    def _is_bot_message(self, message: Dict) -> bool:
        """
        Check if a message is from a bot
        """
        return (
            message.get('bot_id') is not None or
            message.get('subtype') == 'bot_message' or
            'bot_profile' in message
        )

    def _message_exists(self, ts: str) -> bool:
        """
        Check if message already exists in database
        """
        existing = self.db_session.query(SlackMessage).filter_by(ts=ts).first()
        return existing is not None

    def _store_message(self, message: Dict, channel_id: str) -> None:
        """
        Store a message in the database
        """
        try:
            user_info = self._get_user_info(message.get('user'))

            slack_message = SlackMessage(
                ts=message['ts'],
                channel_id=channel_id,
                thread_ts=message.get('thread_ts'),
                user_id=message.get('user'),
                username=user_info.get('real_name') if user_info else None,
                text=message.get('text', ''),
                message_type=message.get('type', 'message'),

                sent_timestamp=float(message['ts']),
                sent_datetime=datetime.fromtimestamp(float(message['ts'])),

                retrieved_at=datetime.utcnow(),
                processed=False,

                attachments=message.get('attachments'),
                blocks=message.get('blocks'),
                files=message.get('files'),
                reactions=message.get('reactions'),

                is_bot=self._is_bot_message(message),
                bot_id=message.get('bot_id'),

                edited_ts=message.get('edited', {}).get('ts'),
                edited_user=message.get('edited', {}).get('user'),

                reply_count=message.get('reply_count', 0),
                reply_users_count=message.get('reply_users_count', 0),

                raw_data=message
            )

            self.db_session.add(slack_message)

        except Exception as e:
            logger.error(f"Error storing message {message.get('ts')}: {str(e)}")

    def _get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user information from Slack
        """
        if not user_id:
            return None

        try:
            response = self.client.users_info(user=user_id)
            return response.get('user')
        except:
            return None

    def get_unprocessed_messages(self, limit: int = 100) -> List[SlackMessage]:
        """
        Get messages that haven't been processed yet
        """
        return self.db_session.query(SlackMessage)\
            .filter_by(processed=False)\
            .order_by(SlackMessage.sent_datetime)\
            .limit(limit)\
            .all()

    def mark_message_processed(self, ts: str) -> None:
        """
        Mark a message as processed
        """
        message = self.db_session.query(SlackMessage).filter_by(ts=ts).first()
        if message:
            message.processed = True
            message.processed_at = datetime.utcnow()
            self.db_session.commit()

    def mark_report_generated(self, ts: str, report_content: str = None) -> None:
        """
        Mark that a report has been generated for this message
        """
        message = self.db_session.query(SlackMessage).filter_by(ts=ts).first()
        if message:
            message.report_generated = True
            message.report_generated_at = datetime.utcnow()
            if report_content:
                message.report_content = report_content
            self.db_session.commit()
            logger.info(f"Report marked as generated for message {ts}")

    def mark_report_sent_to_slack(self, ts: str, thread_ts: str = None) -> None:
        """
        Mark that a report has been sent to Slack
        """
        message = self.db_session.query(SlackMessage).filter_by(ts=ts).first()
        if message:
            message.report_sent_to_slack = True
            message.report_sent_at = datetime.utcnow()
            if thread_ts:
                message.report_thread_ts = thread_ts
            self.db_session.commit()
            logger.info(f"Report marked as sent to Slack for message {ts}")

    def get_messages_needing_reports(self, limit: int = 10) -> List[SlackMessage]:
        """
        Get messages that have been processed but haven't had reports generated
        """
        return self.db_session.query(SlackMessage)\
            .filter_by(processed=True, report_generated=False, is_bot=False)\
            .order_by(SlackMessage.sent_datetime)\
            .limit(limit)\
            .all()

    def get_messages_with_unsent_reports(self, limit: int = 10) -> List[SlackMessage]:
        """
        Get messages that have reports generated but not sent to Slack
        """
        return self.db_session.query(SlackMessage)\
            .filter_by(report_generated=True, report_sent_to_slack=False)\
            .order_by(SlackMessage.report_generated_at)\
            .limit(limit)\
            .all()

    def get_messages_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_only: bool = True
    ) -> List[SlackMessage]:
        """
        Get messages within a date range
        """
        query = self.db_session.query(SlackMessage)\
            .filter(SlackMessage.sent_datetime >= start_date)\
            .filter(SlackMessage.sent_datetime <= end_date)

        if user_only:
            query = query.filter_by(is_bot=False)

        return query.order_by(SlackMessage.sent_datetime).all()

    def get_retrieval_stats(self, days_back: int = 7) -> Dict:
        """
        Get retrieval statistics for the past N days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        logs = self.db_session.query(MessageRetrievalLog)\
            .filter(MessageRetrievalLog.retrieval_started_at >= cutoff_date)\
            .order_by(MessageRetrievalLog.retrieval_started_at.desc())\
            .all()

        total_messages = self.db_session.query(SlackMessage)\
            .filter(SlackMessage.retrieved_at >= cutoff_date)\
            .count()

        unprocessed = self.db_session.query(SlackMessage)\
            .filter_by(processed=False)\
            .count()

        messages_needing_reports = self.db_session.query(SlackMessage)\
            .filter_by(processed=True, report_generated=False, is_bot=False)\
            .count()

        unsent_reports = self.db_session.query(SlackMessage)\
            .filter_by(report_generated=True, report_sent_to_slack=False)\
            .count()

        total_reports_generated = self.db_session.query(SlackMessage)\
            .filter_by(report_generated=True)\
            .count()

        total_reports_sent = self.db_session.query(SlackMessage)\
            .filter_by(report_sent_to_slack=True)\
            .count()

        return {
            'total_retrievals': len(logs),
            'successful_retrievals': len([l for l in logs if l.status == 'completed']),
            'failed_retrievals': len([l for l in logs if l.status == 'failed']),
            'total_messages_retrieved': total_messages,
            'unprocessed_messages': unprocessed,
            'messages_needing_reports': messages_needing_reports,
            'unsent_reports': unsent_reports,
            'total_reports_generated': total_reports_generated,
            'total_reports_sent': total_reports_sent,
            'retrieval_logs': logs
        }

    def close(self):
        """
        Close database session
        """
        self.db_session.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized. SlackMessageRetriever ready for use.")