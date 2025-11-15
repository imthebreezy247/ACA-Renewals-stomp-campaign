#!/usr/bin/env python3
"""
Interactive script to extract a single email at a time
Allows you to browse and select which email to process
"""

import sys
import os

# Add the current directory to the path so we can import from the main script
sys.path.insert(0, os.path.dirname(__file__))

from extract_all_deals_properly_mcp import LeadExtractor, AGENT_EMAILS
from mcp_functions import search_gmail_messages, read_gmail_thread
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def list_available_emails(max_results=20):
    """List available emails for selection"""

    # Build query for all agents
    agent_queries = [f"from:{email}" for email in AGENT_EMAILS.keys()]
    query = f"({' OR '.join(agent_queries)}) has:attachment"

    logger.info("Searching for emails...")
    results = search_gmail_messages(q=query, max_results=max_results)
    messages = results.get('messages', [])

    return messages


def show_email_preview(thread_id):
    """Show a preview of the email content"""
    thread = read_gmail_thread(thread_id=thread_id, include_full_messages=True)

    messages = thread.get('messages', [])
    if messages:
        first_msg = messages[0]
        headers = {h['name']: h['value'] for h in first_msg.get('payload', {}).get('headers', [])}

        print(f"\nFrom: {headers.get('From', 'Unknown')}")
        print(f"Subject: {headers.get('Subject', 'No Subject')}")
        print(f"Date: {headers.get('Date', 'Unknown')}")
        print(f"Thread ID: {thread_id}")
        print("-" * 70)


def main():
    """Interactive email extraction"""

    print("=" * 70)
    print("SINGLE EMAIL EXTRACTOR")
    print("=" * 70)

    # List available emails
    print("\nSearching for available emails...")
    messages = list_available_emails()

    if not messages:
        print("No emails found!")
        return

    print(f"\nFound {len(messages)} emails")
    print("\n" + "=" * 70)

    # Show list
    for idx, msg in enumerate(messages, 1):
        thread_id = msg.get('threadId')
        snippet = msg.get('snippet', '')[:60]
        print(f"{idx}. {snippet}...")

    print("\n" + "=" * 70)

    # Get user selection
    while True:
        try:
            choice = input(f"\nEnter email number to process (1-{len(messages)}, or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                print("Exiting...")
                return

            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(messages):
                break
            else:
                print(f"Please enter a number between 1 and {len(messages)}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'")

    # Get selected message
    selected_msg = messages[choice_idx]
    thread_id = selected_msg.get('threadId')

    # Show preview
    print("\n" + "=" * 70)
    print("EMAIL PREVIEW")
    print("=" * 70)
    show_email_preview(thread_id)

    # Confirm extraction
    confirm = input("\nProceed with extraction? [Y/n]: ").strip().upper()

    if confirm == 'N':
        print("Cancelled.")
        return

    # Extract
    print("\n" + "=" * 70)
    print("EXTRACTING...")
    print("=" * 70 + "\n")

    extractor = LeadExtractor()

    try:
        lead_data = extractor.extract_client_from_thread(thread_id)

        # Show results
        print("\n" + "=" * 70)
        print("EXTRACTION RESULTS")
        print("=" * 70)

        for key, value in lead_data.items():
            if value is not None and key not in ['thread_id', 'attachments', 'extracted_at']:
                if key == 'policy_numbers' and isinstance(value, list):
                    print(f"  {key:20s}: {', '.join(value)}")
                else:
                    print(f"  {key:20s}: {value}")

        # Show attachments
        if lead_data.get('attachments'):
            print(f"\n  Attachments ({len(lead_data['attachments'])}):")
            for att in lead_data['attachments']:
                print(f"    - {att['filename']}")

        # Ask to save
        print("\n" + "=" * 70)

        if lead_data.get('is_duplicate'):
            print(f"WARNING: This lead is a duplicate (ID: {lead_data.get('duplicate_id')})")
            action = input("\nSave anyway? [y/N]: ").strip().upper()
            if action == 'Y':
                extractor.save_to_supabase(lead_data)
                print("Saved to Supabase!")
            else:
                print("Not saved.")
        else:
            action = input("\nSave to Supabase? [Y/n]: ").strip().upper()
            if action != 'N':
                extractor.save_to_supabase(lead_data)
                print("Saved to Supabase!")
            else:
                print("Not saved.")

        # Export to CSV
        export = input("\nExport to CSV? [Y/n]: ").strip().upper()
        if export != 'N':
            csv_file = extractor.export_to_csv([lead_data])
            print(f"Exported to: {csv_file}")

    except Exception as e:
        print(f"\nERROR: {e}")
        logger.exception("Extraction failed")
        return

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)


if __name__ == '__main__':
    main()
