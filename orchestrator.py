#!/usr/bin/env python3
"""
Deep Research Orchestrator
Coordinates the entire workflow from Slack message retrieval to report generation and delivery
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import schedule
import threading

# Add slack-threads-api to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'slack-threads-api'))

from slack_message_retriever import SlackMessageRetriever
from slack_thread_client import SlackThreadClient
from database_models import get_session, init_database
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeepResearchOrchestrator:
    def __init__(self):
        self.retriever = SlackMessageRetriever()
        self.slack_client = SlackThreadClient()
        self.db_session = get_session()
        self.base_dir = Path(__file__).parent
        self.playwright_dir = self.base_dir / "playwright-mcp-state"
        self.retrieve_report_dir = self.base_dir / "retrieve_report"
        self.pending_reports = {}  # Store URL -> message mapping for delayed processing

    def step1_retrieve_slack_messages(self):
        """Step 1: Retrieve new messages from Slack and update database"""
        logger.info("=" * 60)
        logger.info("STEP 1: Retrieving new messages from Slack")
        logger.info("=" * 60)

        try:
            # Retrieve messages from the past 24 hours by default
            stats = self.retriever.get_channel_messages(
                hours_back=24,
                include_threads=True,
                user_only=True  # Only get user messages, not bot messages
            )

            logger.info(f"Retrieved {stats['new_messages_added']} new messages")
            logger.info(f"Skipped {stats['duplicate_messages_skipped']} duplicates")
            logger.info(f"Filtered {stats['bot_messages_filtered']} bot messages")

            return True

        except Exception as e:
            logger.error(f"Error retrieving Slack messages: {e}")
            return False

    def step2_get_oldest_unprocessed_message(self):
        """Step 2: Get the oldest unprocessed message from database"""
        logger.info("=" * 60)
        logger.info("STEP 2: Finding oldest unprocessed message")
        logger.info("=" * 60)

        try:
            # Query for oldest unprocessed message
            from database_models import SlackMessage

            message = self.db_session.query(SlackMessage).filter(
                SlackMessage.processed == False,
                SlackMessage.is_bot == False
            ).order_by(
                SlackMessage.sent_datetime.asc()
            ).first()

            if message:
                logger.info(f"Found unprocessed message from {message.username}: {message.text[:100]}...")
                return message
            else:
                logger.info("No unprocessed messages found")
                return None

        except Exception as e:
            logger.error(f"Error getting unprocessed message: {e}")
            return None

    def step3_generate_deep_research(self, message):
        """Step 3: Run deep research with the message content"""
        logger.info("=" * 60)
        logger.info("STEP 3: Generating Deep Research report")
        logger.info("=" * 60)

        try:
            # Prepare the search query from the message
            search_query = message.text

            # Create modified version of deep-research script
            script_path = self.playwright_dir / "deep-research-dynamic.js"

            # Read the original script
            original_script_path = self.playwright_dir / "deep-research-with-start.js"
            with open(original_script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Replace the hardcoded search query with the message content
            old_query = 'const searchQuery = "Deep research for Lemmings the game and being stuck with the same tool or approach in problem-solving";'
            new_query = f'const searchQuery = "{search_query.replace('"', '\\"')}";'

            script_content = script_content.replace(old_query, new_query)

            # Write the modified script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            logger.info(f"Running deep research for: {search_query[:100]}...")

            # Execute the script
            result = subprocess.run(
                ["node", str(script_path)],
                cwd=str(self.playwright_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Deep research script completed successfully")

                # Read the captured URL
                url_file = self.playwright_dir / "deep-research-start-url.json"
                if url_file.exists():
                    with open(url_file, 'r') as f:
                        url_data = json.load(f)
                        report_url = url_data.get('reportUrl', url_data.get('url'))

                    logger.info(f"Captured report URL: {report_url}")
                    return report_url
                else:
                    logger.error("URL file not found after deep research")
                    return None
            else:
                logger.error(f"Deep research script failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Deep research script timed out")
            return None
        except Exception as e:
            logger.error(f"Error in deep research generation: {e}")
            return None

    def step4_schedule_report_retrieval(self, url, message):
        """Step 4: Schedule report retrieval for 20 minutes later"""
        logger.info("=" * 60)
        logger.info("STEP 4: Scheduling report retrieval")
        logger.info("=" * 60)

        # Store the URL and message for later processing
        self.pending_reports[url] = message

        # Schedule the retrieval
        retrieval_time = datetime.now() + timedelta(minutes=20)
        logger.info(f"Report retrieval scheduled for {retrieval_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Use threading to schedule the delayed task
        timer = threading.Timer(1200, self.step5_retrieve_and_send_report, args=[url, message])
        timer.daemon = True
        timer.start()

        return True

    def step5_retrieve_and_send_report(self, url, message):
        """Step 5: Retrieve the complete report and send to Slack"""
        logger.info("=" * 60)
        logger.info("STEP 5: Retrieving and sending report")
        logger.info("=" * 60)

        try:
            # Run the retrieve_report script
            logger.info(f"Retrieving report from: {url}")

            result = subprocess.run(
                ["node", "retrieve_report.js", url],
                cwd=str(self.retrieve_report_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120  # 2 minute timeout
            )

            if result.returncode == 0:
                logger.info("Report retrieved successfully")

                # Find the latest report file
                reports_dir = self.retrieve_report_dir / "reports"
                report_files = list(reports_dir.glob("report_*.txt"))

                if report_files:
                    # Get the most recent report
                    latest_report = max(report_files, key=lambda f: f.stat().st_mtime)

                    with open(latest_report, 'r', encoding='utf-8') as f:
                        report_content = f.read()

                    logger.info(f"Read report from {latest_report.name}")

                    # Send report to Slack
                    self.send_report_to_slack(report_content, message)

                    # Message was already marked as processed when URL was retrieved
                    logger.info("Report sent successfully for already-processed message")

                else:
                    logger.error("No report files found")

            else:
                logger.error(f"Report retrieval failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Error in report retrieval and sending: {e}")

        finally:
            # Remove from pending reports
            if url in self.pending_reports:
                del self.pending_reports[url]
                logger.info("Report processing completed and removed from pending queue")

    def send_report_to_slack(self, report_content, original_message):
        """Send the report to Slack as a reply or new message"""
        try:
            # Truncate report if too long (Slack has a 40000 character limit)
            if len(report_content) > 39000:
                report_content = report_content[:39000] + "\n\n... [Report truncated due to length]"

            # Create a formatted message
            formatted_message = f"""📊 **Deep Research Report Generated**

Original Request: {original_message.text[:200]}...
Requested by: @{original_message.username}
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{report_content}"""

            # Send to Slack
            if original_message.thread_ts:
                # Reply to existing thread
                response = self.slack_client.reply_to_thread(
                    thread_ts=original_message.thread_ts,
                    text=formatted_message
                )
            else:
                # Create new message
                response = self.slack_client.send_message(
                    text=formatted_message,
                    channel=original_message.channel_id
                )

            if response and response.get('ok'):
                logger.info(f"Report sent to Slack successfully")

                # Update database with report details
                from database_models import SlackMessage

                db_message = self.db_session.query(SlackMessage).filter(
                    SlackMessage.ts == original_message.ts
                ).first()

                if db_message:
                    db_message.report_sent_to_slack = True
                    db_message.report_sent_at = datetime.utcnow()
                    db_message.report_thread_ts = response.get('ts')
                    self.db_session.commit()

            else:
                logger.error("Failed to send report to Slack")

        except Exception as e:
            logger.error(f"Error sending report to Slack: {e}")

    def mark_message_processed(self, message, report_url=None, success=True):
        """Mark a message as processed in the database"""
        try:
            from database_models import SlackMessage

            db_message = self.db_session.query(SlackMessage).filter(
                SlackMessage.ts == message.ts
            ).first()

            if db_message:
                # Only mark as processed if successful
                if success:
                    db_message.processed = True
                    db_message.processed_at = datetime.utcnow()
                    db_message.report_generated = True
                    db_message.report_generated_at = datetime.utcnow()

                    if report_url:
                        # Store URL in report_content field
                        db_message.report_content = f"Report URL: {report_url}"
                else:
                    # Keep as unprocessed so it can be retried
                    db_message.processed = False
                    logger.info(f"Message {message.ts} kept as unprocessed for retry")

                self.db_session.commit()
                if success:
                    logger.info(f"Message {message.ts} marked as processed")

        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")
            self.db_session.rollback()

    def run_workflow(self):
        """Run the complete workflow"""
        logger.info("\n" + "=" * 60)
        logger.info("STARTING DEEP RESEARCH ORCHESTRATOR WORKFLOW")
        logger.info("=" * 60 + "\n")

        # Step 1: Retrieve new Slack messages
        if not self.step1_retrieve_slack_messages():
            logger.error("Failed to retrieve Slack messages. Stopping workflow.")
            return False

        # Step 2: Get oldest unprocessed message
        message = self.step2_get_oldest_unprocessed_message()
        if not message:
            logger.info("No messages to process. Workflow complete.")
            return True

        # Step 3: Generate deep research
        report_url = self.step3_generate_deep_research(message)
        if not report_url:
            logger.error("Failed to generate deep research. Message will be retried on next run.")
            # DO NOT mark as processed - leave it for retry
            return False

        # Mark message as processed immediately after getting URL
        self.mark_message_processed(message, report_url=report_url, success=True)
        logger.info("Message marked as processed after URL retrieval")

        # Step 4: Schedule report retrieval for 20 minutes later
        self.step4_schedule_report_retrieval(report_url, message)

        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW INITIATED SUCCESSFULLY")
        logger.info(f"Report retrieval scheduled for 20 minutes from now")
        logger.info("The orchestrator will continue running to handle the scheduled task")
        logger.info("=" * 60 + "\n")

        return True

    def run_continuous(self, interval_minutes=30):
        """Run the orchestrator continuously, checking for new messages every interval"""
        logger.info(f"Starting continuous orchestrator (checking every {interval_minutes} minutes)")

        # Run immediately
        self.run_workflow()

        # Schedule periodic runs
        schedule.every(interval_minutes).minutes.do(self.run_workflow)

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user")
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")


def main():
    """Main entry point"""
    # Initialize database if needed
    init_database()

    # Create and run orchestrator
    orchestrator = DeepResearchOrchestrator()

    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Run continuously
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        orchestrator.run_continuous(interval)
    else:
        # Run once
        result = orchestrator.run_workflow()

        # If a report was scheduled, wait for it to complete
        if orchestrator.pending_reports:
            logger.info("Waiting for scheduled report retrieval (20 minutes)...")
            logger.info("The process will exit automatically after report is sent")

            # Wait for up to 25 minutes (20 min + 5 min buffer for processing)
            max_wait = 1500  # 25 minutes in seconds
            start_time = time.time()

            while orchestrator.pending_reports and (time.time() - start_time) < max_wait:
                time.sleep(10)  # Check every 10 seconds

            if orchestrator.pending_reports:
                logger.warning("Report retrieval timed out after 25 minutes")
            else:
                logger.info("All scheduled tasks completed successfully")
        else:
            logger.info("No reports to process. Exiting.")


if __name__ == "__main__":
    main()