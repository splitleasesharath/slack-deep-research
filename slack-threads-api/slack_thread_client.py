import logging
from typing import Optional, Dict, List, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackThreadClient:
    def __init__(self, token: str = None):
        self.token = token or Config.SLACK_BOT_TOKEN
        self.client = WebClient(token=self.token)
        self.default_channel = Config.SLACK_CHANNEL_ID
        self.active_threads = {}

    def send_message(
        self,
        text: str,
        channel: str = None,
        thread_ts: str = None,
        blocks: List[Dict] = None,
        attachments: List[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to Slack channel or thread

        Args:
            text: Message text
            channel: Channel ID (defaults to configured channel)
            thread_ts: Thread timestamp for threading
            blocks: Slack blocks for rich formatting
            attachments: Message attachments

        Returns:
            Response with thread_ts for future replies
        """
        try:
            channel = channel or self.default_channel

            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts,
                blocks=blocks,
                attachments=attachments
            )

            result = {
                'ok': True,
                'channel': response['channel'],
                'ts': response['ts'],
                'thread_ts': thread_ts or response['ts'],
                'message': response.get('message', {})
            }

            if not thread_ts:
                logger.info(f"New message sent. Thread ID: {response['ts']}")
                self.active_threads[response['ts']] = {
                    'channel': channel,
                    'initial_message': text[:100]
                }
            else:
                logger.info(f"Reply added to thread: {thread_ts}")

            return result

        except SlackApiError as e:
            logger.error(f"Slack API Error: {e.response['error']}")
            return {'ok': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return {'ok': False, 'error': str(e)}

    def start_thread(
        self,
        initial_message: str,
        channel: str = None,
        blocks: List[Dict] = None
    ) -> Optional[str]:
        """
        Create a new thread and return thread_ts for future replies

        Args:
            initial_message: The first message in the thread
            channel: Channel ID
            blocks: Slack blocks for rich formatting

        Returns:
            Thread timestamp (use this for future replies)
        """
        response = self.send_message(
            text=initial_message,
            channel=channel,
            blocks=blocks
        )

        if response and response.get('ok'):
            thread_ts = response['ts']
            logger.info(f"Thread started with ID: {thread_ts}")
            return thread_ts
        return None

    def reply_to_thread(
        self,
        thread_ts: str,
        text: str,
        channel: str = None,
        blocks: List[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Reply to an existing thread using thread_ts

        Args:
            thread_ts: Thread timestamp from initial message
            text: Reply message text
            channel: Channel ID (must match original thread channel)
            blocks: Slack blocks for rich formatting

        Returns:
            Response from Slack API
        """
        if thread_ts in self.active_threads:
            channel = channel or self.active_threads[thread_ts]['channel']
        else:
            channel = channel or self.default_channel

        return self.send_message(
            text=text,
            channel=channel,
            thread_ts=thread_ts,
            blocks=blocks
        )

    def send_batch_to_thread(
        self,
        thread_ts: str,
        messages: List[str],
        channel: str = None,
        delay_seconds: float = 0.5
    ) -> List[Dict]:
        """
        Send multiple messages to a thread

        Args:
            thread_ts: Thread timestamp
            messages: List of message texts
            channel: Channel ID
            delay_seconds: Delay between messages

        Returns:
            List of responses
        """
        import time
        responses = []

        for message in messages:
            response = self.reply_to_thread(
                thread_ts=thread_ts,
                text=message,
                channel=channel
            )
            responses.append(response)
            if delay_seconds > 0 and message != messages[-1]:
                time.sleep(delay_seconds)

        return responses

    def get_thread_replies(
        self,
        channel: str,
        thread_ts: str,
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """
        Get all replies in a thread

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages in the thread
        """
        try:
            response = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=limit
            )

            messages = response.get('messages', [])
            logger.info(f"Retrieved {len(messages)} messages from thread {thread_ts}")
            return messages

        except SlackApiError as e:
            logger.error(f"Error fetching thread replies: {e.response['error']}")
            return None

    def get_active_threads(self) -> Dict:
        """
        Get all active thread IDs stored in memory

        Returns:
            Dictionary of active threads with their metadata
        """
        return self.active_threads

    def upload_file(
        self,
        file_path: str = None,
        file_content: bytes = None,
        filename: str = None,
        channel: str = None,
        thread_ts: str = None,
        initial_comment: str = None,
        title: str = None
    ) -> Optional[Dict]:
        """
        Upload a file or image to Slack channel or thread

        Args:
            file_path: Path to local file (use this OR file_content)
            file_content: File bytes content (use this OR file_path)
            filename: Name for the file (required if using file_content)
            channel: Channel ID
            thread_ts: Thread timestamp for threading
            initial_comment: Comment with the file
            title: File title

        Returns:
            Response from Slack API or None on error
        """
        try:
            channel = channel or self.default_channel

            upload_kwargs = {
                'channels': channel,
                'initial_comment': initial_comment,
                'title': title
            }

            if thread_ts:
                upload_kwargs['thread_ts'] = thread_ts

            if file_path:
                # Upload from file path using files_upload_v2 (requires files:read)
                response = self.client.files_upload_v2(
                    file=file_path,
                    **upload_kwargs
                )
                logger.info(f"File uploaded from path: {file_path}")
            elif file_content and filename:
                # Upload from bytes content using files_upload_v2
                response = self.client.files_upload_v2(
                    content=file_content,
                    filename=filename,
                    **upload_kwargs
                )
                logger.info(f"File uploaded from content: {filename}")
            else:
                logger.error("Must provide either file_path or (file_content + filename)")
                return None

            if response.get('ok'):
                file_info = response.get('file', {})
                result = {
                    'ok': True,
                    'file_id': file_info.get('id'),
                    'url': file_info.get('url_private'),
                    'permalink': file_info.get('permalink'),
                    'thread_ts': thread_ts
                }

                if thread_ts:
                    logger.info(f"File uploaded to thread: {thread_ts}")
                else:
                    logger.info(f"File uploaded to channel: {channel}")

                return result

        except SlackApiError as e:
            logger.error(f"Error uploading file: {e.response['error']}")
            return {'ok': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            return {'ok': False, 'error': str(e)}