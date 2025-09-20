#!/usr/bin/env python3
"""
Configuration checker for the Deep Research Orchestrator
Ensures all required settings are in place before running
"""

import os
import sys
from pathlib import Path


def check_configuration():
    """Check if all required configuration is in place"""

    print("=" * 60)
    print("CONFIGURATION CHECK")
    print("=" * 60)

    issues = []
    warnings = []

    # Check for .env file in slack-threads-api
    env_file = Path(__file__).parent / "slack-threads-api" / ".env"

    if not env_file.exists():
        issues.append(f"Missing .env file at: {env_file}")
        print(f"[X] .env file not found")

        # Create from example if available
        example_file = env_file.parent / ".env.example"
        if example_file.exists():
            print(f"[+] Creating .env from .env.example")
            print(f"   Please edit {env_file} with your Slack credentials")

            with open(example_file, 'r') as f:
                example_content = f.read()

            with open(env_file, 'w') as f:
                f.write(example_content)
    else:
        print(f"[OK] .env file found")

        # Check if it has actual values (not just placeholders)
        with open(env_file, 'r') as f:
            content = f.read()

        if 'xoxb-your-bot-token' in content:
            warnings.append("[!] .env file contains placeholder values. Please update with real Slack credentials")
            print("[!] .env file needs to be configured with actual Slack credentials")
        else:
            print("[OK] .env file appears to be configured")

    # Check for required directories
    dirs_to_check = [
        ("playwright-mcp-state", "Playwright automation scripts"),
        ("retrieve_report", "Report retrieval module"),
        ("slack-threads-api", "Slack API integration"),
        ("playwright-mcp-state/chrome-persistent-profile", "Chrome persistent profile")
    ]

    print("\nChecking directories:")
    for dir_path, description in dirs_to_check:
        full_path = Path(__file__).parent / dir_path
        if full_path.exists():
            print(f"[OK] {dir_path} - {description}")
        else:
            issues.append(f"Missing directory: {dir_path} ({description})")
            print(f"[X] {dir_path} - {description}")

    # Check for key files
    files_to_check = [
        ("playwright-mcp-state/deep-research-with-start.js", "Deep research automation script"),
        ("retrieve_report/retrieve_report.js", "Report retrieval script"),
        ("slack-threads-api/slack_thread_client.py", "Slack client module"),
        ("orchestrator.py", "Main orchestrator script")
    ]

    print("\nChecking key files:")
    for file_path, description in files_to_check:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"[OK] {file_path}")
        else:
            issues.append(f"Missing file: {file_path} ({description})")
            print(f"[X] {file_path}")

    # Check Python modules
    print("\nChecking Python dependencies:")
    required_modules = [
        ("slack_sdk", "slack-sdk"),
        ("dotenv", "python-dotenv"),
        ("sqlalchemy", "SQLAlchemy"),
        ("schedule", "schedule")
    ]

    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"[OK] {package_name}")
        except ImportError:
            warnings.append(f"Missing Python package: {package_name}")
            print(f"[!] {package_name} - needs to be installed")

    # Summary
    print("\n" + "=" * 60)

    if issues:
        print("[X] CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nThese issues must be resolved before running the orchestrator.")
        return False

    if warnings:
        print("[!] WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
        print("\nThe orchestrator may not work properly until these are addressed.")
        return False

    print("[OK] ALL CHECKS PASSED!")
    print("The orchestrator is ready to run.")
    return True

if __name__ == "__main__":
    if check_configuration():
        sys.exit(0)
    else:
        sys.exit(1)