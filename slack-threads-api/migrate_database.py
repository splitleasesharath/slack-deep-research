#!/usr/bin/env python3
"""
Database migration script to add report tracking fields
"""

import sys
import logging
from sqlalchemy import create_engine, text, inspect
from config import Config
from database_models import Base, get_database_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_existing_columns(engine):
    """Check which columns already exist"""
    inspector = inspect(engine)

    try:
        columns = [col['name'] for col in inspector.get_columns('slack_messages')]
        return columns
    except:
        return []


def migrate_database():
    """Add new report tracking columns to existing database"""

    engine = get_database_engine()
    existing_columns = check_existing_columns(engine)

    if not existing_columns:
        logger.error("Table 'slack_messages' does not exist. Run 'python retrieve_messages.py --init-db' first.")
        return False

    migrations_needed = []

    # Check for report_generated fields
    if 'report_generated' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_generated BOOLEAN DEFAULT FALSE"
        )
        logger.info("Will add column: report_generated")

    if 'report_generated_at' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_generated_at DATETIME"
        )
        logger.info("Will add column: report_generated_at")

    if 'report_content' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_content TEXT"
        )
        logger.info("Will add column: report_content")

    # Check for report_sent_to_slack fields
    if 'report_sent_to_slack' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_sent_to_slack BOOLEAN DEFAULT FALSE"
        )
        logger.info("Will add column: report_sent_to_slack")

    if 'report_sent_at' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_sent_at DATETIME"
        )
        logger.info("Will add column: report_sent_at")

    if 'report_thread_ts' not in existing_columns:
        migrations_needed.append(
            "ALTER TABLE slack_messages ADD COLUMN report_thread_ts VARCHAR(20)"
        )
        logger.info("Will add column: report_thread_ts")

    if not migrations_needed:
        logger.info("Database is already up to date. No migrations needed.")
        return True

    # Execute migrations
    logger.info(f"Executing {len(migrations_needed)} migrations...")

    with engine.connect() as conn:
        for migration in migrations_needed:
            try:
                conn.execute(text(migration))
                conn.commit()
                logger.info(f"✅ Migration successful: {migration[:50]}...")
            except Exception as e:
                logger.error(f"❌ Migration failed: {migration[:50]}...")
                logger.error(f"   Error: {str(e)}")
                return False

    # Create indexes
    try:
        with engine.connect() as conn:
            # Check if indexes exist before creating
            existing_indexes = [idx['name'] for idx in inspect(engine).get_indexes('slack_messages')]

            if 'idx_report_generated' not in existing_indexes:
                conn.execute(text(
                    "CREATE INDEX idx_report_generated ON slack_messages(report_generated)"
                ))
                conn.commit()
                logger.info("✅ Created index: idx_report_generated")

            if 'idx_report_sent' not in existing_indexes:
                conn.execute(text(
                    "CREATE INDEX idx_report_sent ON slack_messages(report_sent_to_slack)"
                ))
                conn.commit()
                logger.info("✅ Created index: idx_report_sent")
    except Exception as e:
        logger.warning(f"Could not create indexes (may already exist): {e}")

    logger.info("✅ Database migration completed successfully!")
    return True


def drop_and_recreate():
    """Drop and recreate all tables (WARNING: Deletes all data!)"""

    response = input("⚠️  WARNING: This will DELETE ALL DATA. Are you sure? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        logger.info("Operation cancelled.")
        return

    engine = get_database_engine()

    logger.info("Dropping all tables...")
    Base.metadata.drop_all(engine)

    logger.info("Creating new tables with updated schema...")
    Base.metadata.create_all(engine)

    logger.info("✅ Database recreated with new schema.")


def show_schema():
    """Display current database schema"""

    engine = get_database_engine()
    inspector = inspect(engine)

    if 'slack_messages' not in inspector.get_table_names():
        logger.error("Table 'slack_messages' does not exist.")
        return

    print("\n=== Current Schema for 'slack_messages' ===\n")

    columns = inspector.get_columns('slack_messages')
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f"DEFAULT {col['default']}" if col.get('default') else ""
        print(f"  {col['name']:25} {str(col['type']):20} {nullable:10} {default}")

    print("\n=== Indexes ===\n")
    indexes = inspector.get_indexes('slack_messages')
    for idx in indexes:
        print(f"  {idx['name']:30} on {', '.join(idx['column_names'])}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database migration tool')
    parser.add_argument('--migrate', action='store_true', help='Run migrations')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate tables (WARNING: Deletes data!)')
    parser.add_argument('--schema', action='store_true', help='Show current schema')

    args = parser.parse_args()

    if args.recreate:
        drop_and_recreate()
    elif args.schema:
        show_schema()
    elif args.migrate:
        success = migrate_database()
        sys.exit(0 if success else 1)
    else:
        # Default action: migrate
        success = migrate_database()
        sys.exit(0 if success else 1)