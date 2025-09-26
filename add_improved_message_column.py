#!/usr/bin/env python3
"""
Database migration script to add improved_message column to existing database
"""

import sqlite3
import sys
from pathlib import Path

def add_improved_message_column():
    """Add the improved_message column to the slack_messages table"""

    # Database path
    db_path = Path(__file__).parent / "slack_messages.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(slack_messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'improved_message' in column_names:
            print("Column 'improved_message' already exists in slack_messages table")
            conn.close()
            return True

        # Add the new column
        print("Adding 'improved_message' column to slack_messages table...")
        cursor.execute("ALTER TABLE slack_messages ADD COLUMN improved_message TEXT")

        # Commit changes
        conn.commit()
        print("Successfully added 'improved_message' column")

        # Verify the column was added
        cursor.execute("PRAGMA table_info(slack_messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'improved_message' in column_names:
            print("Verification successful: Column added")
            conn.close()
            return True
        else:
            print("Verification failed: Column not found after adding")
            conn.close()
            return False

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Adding improved_message column")
    print("=" * 60)

    success = add_improved_message_column()

    if success:
        print("\n✅ Migration completed successfully!")
        print("The orchestrator can now use the prompt improvement feature.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
        sys.exit(1)