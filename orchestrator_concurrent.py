#!/usr/bin/env python3
"""
Deep Research Orchestrator - Concurrent Version
Supports multiple instances running simultaneously with proper session management
"""

import os
import sys
import json
import time
import subprocess
import logging
import uuid
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import threading
import filelock

# Add slack-threads-api to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'slack-threads-api'))

from slack_message_retriever import SlackMessageRetriever
from slack_thread_client import SlackThreadClient
from database_models import get_session, init_database
from config import Config

# Configure logging with session ID
def setup_logger(session_id):
    """Setup logger with session-specific formatting"""
    logger = logging.getLogger(f'orchestrator_{session_id}')
    logger.setLevel(logging.INFO)

    # File handler for session-specific log
    fh = logging.FileHandler(f'orchestrator_{session_id}.log')
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter with session ID
    formatter = logging.Formatter(
        f'%(asctime)s - [{session_id[:8]}] - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class ConcurrentDeepResearchOrchestrator:
    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logger = setup_logger(self.session_id)
        self.retriever = SlackMessageRetriever()
        self.slack_client = SlackThreadClient()
        self.db_session = get_session()
        self.base_dir = Path(__file__).parent
        self.playwright_dir = self.base_dir / "playwright-mcp-state"
        self.retrieve_report_dir = self.base_dir / "retrieve_report"
        self.sessions_dir = self.base_dir / "orchestrator_sessions"
        self.sessions_dir.mkdir(exist_ok=True)

        # Session-specific paths
        self.session_file = self.sessions_dir / f"session_{self.session_id}.json"
        self.lock_file = self.base_dir / "orchestrator.lock"

        self.logger.info(f"Initialized orchestrator session: {self.session_id}")

    def save_session(self, data):
        """Save session data to file"""
        with open(self.session_file, 'w') as f:
            json.dump({
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'data': data
            }, f, indent=2)

    def step1_retrieve_slack_messages(self):
        """Step 1: Retrieve new messages from Slack (can run concurrently)"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 1: Retrieving new messages from Slack")
        self.logger.info("=" * 60)

        try:
            stats = self.retriever.get_channel_messages(
                hours_back=24,
                include_threads=True,
                user_only=True
            )

            self.logger.info(f"Retrieved {stats['new_messages_added']} new messages")
            self.logger.info(f"Skipped {stats['duplicate_messages_skipped']} duplicates")
            self.logger.info(f"Filtered {stats['bot_messages_filtered']} bot messages")

            return True

        except Exception as e:
            self.logger.error(f"Error retrieving Slack messages: {e}")
            return False

    def step2_get_and_lock_unprocessed_message(self):
        """Step 2: Get and lock an unprocessed message atomically"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 2: Finding and locking unprocessed message")
        self.logger.info("=" * 60)

        # Use file lock to ensure only one process grabs a message
        lock = filelock.FileLock(str(self.lock_file), timeout=10)

        try:
            with lock:
                from database_models import SlackMessage

                # Find oldest unprocessed message
                message = self.db_session.query(SlackMessage).filter(
                    SlackMessage.processed == False,
                    SlackMessage.is_bot == False
                ).order_by(
                    SlackMessage.sent_datetime.asc()
                ).first()

                if message:
                    # Check if this is a system message
                    system_message_patterns = [
                        "has joined the channel",
                        "has left the channel",
                        "set the channel topic",
                        "set the channel description",
                        "pinned a message",
                        "unpinned a message",
                        "archived the channel",
                        "unarchived the channel",
                        "renamed the channel",
                        "set the channel purpose",
                        "cleared the channel topic",
                        "cleared the channel purpose"
                    ]

                    is_system_message = any(pattern in message.text.lower() for pattern in system_message_patterns)

                    if is_system_message:
                        self.logger.info(f"Skipping system message: {message.text[:100]}...")
                        # Mark as processed to skip it permanently
                        message.processed = True
                        message.processed_at = datetime.utcnow()
                        self.db_session.commit()
                        # Return None to try next message
                        return None

                    # Immediately mark as processed to prevent other instances from taking it
                    message.processed = True
                    message.processed_at = datetime.utcnow()
                    self.db_session.commit()

                    self.logger.info(f"Locked message from {message.username}: {message.text[:100]}...")

                    # Return a detached copy of the message
                    return {
                        'ts': message.ts,
                        'text': message.text,
                        'username': message.username,
                        'channel_id': message.channel_id,
                        'thread_ts': message.thread_ts
                    }
                else:
                    self.logger.info("No unprocessed messages found")
                    return None

        except filelock.Timeout:
            self.logger.warning("Could not acquire lock - another process may be running")
            return None
        except Exception as e:
            self.logger.error(f"Error getting unprocessed message: {e}")
            self.db_session.rollback()
            return None

    def step3_generate_deep_research(self, message):
        """Step 3: Run deep research with session-specific script"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 3: Generating Deep Research report")
        self.logger.info("=" * 60)

        try:
            search_query = message['text']

            # Create session-specific script file
            script_path = self.playwright_dir / f"deep-research-{self.session_id[:8]}.js"

            # Read the original script
            original_script_path = self.playwright_dir / "deep-research-with-start.js"
            with open(original_script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Replace the hardcoded search query
            old_query = 'const searchQuery = "Deep research for Lemmings the game and being stuck with the same tool or approach in problem-solving";'
            new_query = f'const searchQuery = "{search_query.replace('"', '\\"')}";'
            script_content = script_content.replace(old_query, new_query)

            # Write session-specific script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            self.logger.info(f"Running deep research for: {search_query[:100]}...")

            # Execute the script
            result = subprocess.run(
                ["node", str(script_path)],
                cwd=str(self.playwright_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )

            # Clean up session script
            try:
                script_path.unlink()
            except:
                pass

            if result.returncode == 0:
                self.logger.info("Deep research script completed successfully")

                # Read the captured URL
                url_file = self.playwright_dir / "deep-research-start-url.json"
                if url_file.exists():
                    with open(url_file, 'r') as f:
                        url_data = json.load(f)
                        report_url = url_data.get('reportUrl', url_data.get('url'))

                    self.logger.info(f"Captured report URL: {report_url}")
                    return report_url
                else:
                    self.logger.error("URL file not found after deep research")
                    return None
            else:
                self.logger.error(f"Deep research script failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("Deep research script timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error in deep research generation: {e}")
            return None

    def step4_schedule_report_retrieval(self, url, message):
        """Step 4: Schedule report retrieval with session tracking"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 4: Scheduling report retrieval")
        self.logger.info("=" * 60)

        # Save session data for tracking
        self.save_session({
            'url': url,
            'message': message,
            'scheduled_at': datetime.now().isoformat(),
            'scheduled_for': (datetime.now() + timedelta(minutes=20)).isoformat()
        })

        retrieval_time = datetime.now() + timedelta(minutes=20)
        self.logger.info(f"Report retrieval scheduled for {retrieval_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Create a daemon thread for delayed execution
        timer = threading.Timer(1200, self.step5_retrieve_and_send_report, args=[url, message])
        timer.daemon = True
        timer.start()

        return timer

    def step5_retrieve_and_send_report(self, url, message):
        """Step 5: Retrieve report with session-specific handling"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 5: Retrieving and sending report")
        self.logger.info("=" * 60)

        try:
            self.logger.info(f"Retrieving report from: {url}")

            # Create session-specific timestamp for report files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_marker = f"{timestamp}_{self.session_id[:8]}"

            result = subprocess.run(
                ["node", "retrieve_report.js", url],
                cwd=str(self.retrieve_report_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )

            if result.returncode == 0:
                self.logger.info("Report retrieved successfully")

                # Find report files created around this time
                reports_dir = self.retrieve_report_dir / "reports"
                report_files = list(reports_dir.glob("report_*.txt"))

                if report_files:
                    # Get the most recent report (within last 2 minutes)
                    recent_reports = []
                    cutoff_time = time.time() - 120  # 2 minutes ago

                    for report_file in report_files:
                        if report_file.stat().st_mtime > cutoff_time:
                            recent_reports.append(report_file)

                    if recent_reports:
                        latest_report = max(recent_reports, key=lambda f: f.stat().st_mtime)

                        with open(latest_report, 'r', encoding='utf-8') as f:
                            report_content = f.read()

                        self.logger.info(f"Read report from {latest_report.name}")

                        # Send report to Slack
                        self.send_report_to_slack(report_content, message)

                        # Update database
                        self.mark_report_sent(message['ts'], url)
                    else:
                        self.logger.error("No recent report files found")
                else:
                    self.logger.error("No report files found")

            else:
                self.logger.error(f"Report retrieval failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Error in report retrieval and sending: {e}")

        finally:
            # Clean up session file
            if self.session_file.exists():
                try:
                    self.session_file.unlink()
                    self.logger.info("Session file cleaned up")
                except:
                    pass

    def send_report_to_slack(self, report_content, original_message):
        """Send report to Slack"""
        try:
            if len(report_content) > 39000:
                report_content = report_content[:39000] + "\n\n... [Report truncated due to length]"

            formatted_message = f"""📊 **Deep Research Report Generated**

Original Request: {original_message['text'][:200]}...
Requested by: @{original_message['username']}
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session: {self.session_id[:8]}

---

{report_content}"""

            if original_message.get('thread_ts'):
                response = self.slack_client.reply_to_thread(
                    thread_ts=original_message['thread_ts'],
                    text=formatted_message
                )
            else:
                response = self.slack_client.send_message(
                    text=formatted_message,
                    channel=original_message['channel_id']
                )

            if response and response.get('ok'):
                self.logger.info(f"Report sent to Slack successfully")
            else:
                self.logger.error("Failed to send report to Slack")

        except Exception as e:
            self.logger.error(f"Error sending report to Slack: {e}")

    def mark_report_sent(self, message_ts, report_url):
        """Update database to mark report as sent"""
        try:
            from database_models import SlackMessage

            message = self.db_session.query(SlackMessage).filter(
                SlackMessage.ts == message_ts
            ).first()

            if message:
                message.report_generated = True
                message.report_generated_at = datetime.utcnow()
                message.report_sent_to_slack = True
                message.report_sent_at = datetime.utcnow()
                message.report_content = f"Report URL: {report_url}"
                self.db_session.commit()
                self.logger.info(f"Database updated for message {message_ts}")

        except Exception as e:
            self.logger.error(f"Error updating database: {e}")
            self.db_session.rollback()

    def run_workflow(self):
        """Run the complete workflow"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"STARTING ORCHESTRATOR SESSION: {self.session_id[:8]}")
        self.logger.info("=" * 60 + "\n")

        # Step 1: Retrieve new Slack messages
        if not self.step1_retrieve_slack_messages():
            self.logger.error("Failed to retrieve Slack messages")
            return False

        # Step 2: Get and lock an unprocessed message
        message = self.step2_get_and_lock_unprocessed_message()
        if not message:
            self.logger.info("No messages to process")
            return True

        # Step 3: Generate deep research
        report_url = self.step3_generate_deep_research(message)
        if not report_url:
            self.logger.error("Failed to generate deep research")
            return False

        # Step 4: Schedule report retrieval
        timer = self.step4_schedule_report_retrieval(report_url, message)

        self.logger.info("\n" + "=" * 60)
        self.logger.info("WORKFLOW INITIATED SUCCESSFULLY")
        self.logger.info(f"Session {self.session_id[:8]} scheduled for 20 minutes")
        self.logger.info("=" * 60 + "\n")

        return timer

def cleanup_old_sessions(base_dir, max_age_hours=24):
    """Clean up old session files and logs"""
    sessions_dir = base_dir / "orchestrator_sessions"
    if not sessions_dir.exists():
        return

    cutoff_time = time.time() - (max_age_hours * 3600)

    # Clean session files
    for session_file in sessions_dir.glob("session_*.json"):
        if session_file.stat().st_mtime < cutoff_time:
            try:
                session_file.unlink()
            except:
                pass

    # Clean old logs
    for log_file in base_dir.glob("orchestrator_*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
            except:
                pass

def main():
    """Main entry point for concurrent orchestrator"""

    # Install filelock if not present
    try:
        import filelock
    except ImportError:
        print("Installing required package: filelock")
        subprocess.run([sys.executable, "-m", "pip", "install", "filelock"], check=True)
        import filelock

    # Initialize database
    init_database()

    # Clean up old sessions
    base_dir = Path(__file__).parent
    cleanup_old_sessions(base_dir)

    # Create new session
    orchestrator = ConcurrentDeepResearchOrchestrator()

    # Run workflow
    timer = orchestrator.run_workflow()

    if timer and isinstance(timer, threading.Timer):
        # Wait for the scheduled task to complete
        orchestrator.logger.info("Waiting for scheduled report retrieval...")
        timer.join(timeout=1500)  # Wait up to 25 minutes

        if timer.is_alive():
            orchestrator.logger.warning("Report retrieval timed out")
        else:
            orchestrator.logger.info("Session completed successfully")
    else:
        orchestrator.logger.info("No scheduled tasks - exiting")

if __name__ == "__main__":
    main()