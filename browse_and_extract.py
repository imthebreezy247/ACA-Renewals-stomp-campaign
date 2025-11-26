#!/usr/bin/env python3
"""Browse and extract emails one at a time with quick previews."""

import argparse
import importlib.util
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

from mcp_functions import search_gmail_messages


def _load_extract_module(module_path: Path) -> ModuleType:
    """
    Dynamically load the main extractor module.

    Keeping this isolated helps mypy/flake8 and avoids top-level code
    before imports.
    """
    spec = importlib.util.spec_from_file_location(
        "extract_module", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load extractor module specification.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE_DIR = Path(__file__).resolve().parent
EXTRACT_MODULE_PATH = BASE_DIR / "extract_all_deals-properly-mcp.py"
extract_module = _load_extract_module(EXTRACT_MODULE_PATH)
LeadExtractor = extract_module.LeadExtractor
AGENT_EMAILS = extract_module.AGENT_EMAILS
SKIP_KEYS = {"thread_id", "attachments", "extracted_at"}

# Setup logging - suppress INFO messages for cleaner output
logging.basicConfig(level=logging.WARNING, format="%(message)s")


def extract_preview_data(extractor: Any, thread_id: str) -> Dict[str, Any]:
    """Extract key fields from an email for preview."""
    try:
        data = extractor.extract_client_from_thread(thread_id)
        return {
            "thread_id": thread_id,
            "client_name": data.get("client_name", "N/A"),
            "email": data.get("client_email", "N/A"),
            "phone": data.get("client_phone", "N/A"),
            "premium": data.get("monthly_premium", "N/A"),
            "carrier": data.get("carrier", "N/A"),
            "agent": data.get("agent_name", "N/A"),
            "sold_date": data.get("sold_date", "N/A"),
            "attachments": len(data.get("attachments", [])),
            "full_data": data,
        }
    except Exception as e:
        return {
            "thread_id": thread_id,
            "client_name": f"ERROR: {str(e)[:30]}",
            "email": "N/A",
            "phone": "N/A",
            "premium": "N/A",
            "carrier": "N/A",
            "agent": "N/A",
            "sold_date": "N/A",
            "attachments": 0,
            "full_data": None,
        }


def list_all_emails(agent_email: str | None = None) -> List[Dict[str, Any]]:
    """Get all emails, optionally filtered by agent."""

    if agent_email:
        # Single agent
        query = f"from:{agent_email} has:attachment"
        agent_display = AGENT_EMAILS.get(agent_email, agent_email)
        print(f"\nSearching for emails from {agent_display}...")
    else:
        # All agents
        agent_queries = [f"from:{email}" for email in AGENT_EMAILS.keys()]
        query = f"({' OR '.join(agent_queries)}) has:attachment"
        print("\nSearching for emails from ALL agents...")

    # Get ALL messages (set very high limit)
    results = search_gmail_messages(q=query, max_results=1000)
    messages = results.get("messages", [])

    return messages


def display_emails_table(previews: List[Dict[str, Any]]) -> None:
    """Display emails in a formatted table."""

    print("\n" + "=" * 150)
    header = (
        f"{'#':<4} {'Client Name':<25} {'Phone':<15} {'Email':<30} "
        f"{'Premium':<10} {'Carrier':<15} {'Agent':<20} "
        f"{'Sold Date':<12} {'Att':<4}"
    )
    print(header)
    print("=" * 150)

    for idx, preview in enumerate(previews, 1):
        client_name = preview["client_name"][:24]
        phone = preview["phone"][:14]
        email = preview["email"][:29]
        premium = str(preview["premium"])[:9]
        carrier = preview["carrier"][:14]
        agent = preview["agent"][:19]
        sold_date = preview["sold_date"][:11]
        attachments = str(preview["attachments"])

        row = (
            f"{idx:<4} {client_name:<25} {phone:<15} {email:<30} "
            f"{premium:<10} {carrier:<15} {agent:<20} "
            f"{sold_date:<12} {attachments:<4}"
        )
        print(row)

    print("=" * 150)


def main() -> None:
    """Main interactive browser."""

    parser = argparse.ArgumentParser(
        description="Browse and extract emails one at a time"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help=(
            "Filter by agent email "
            "(e.g., danielberman.ushealth@gmail.com)"
        ),
    )
    args = parser.parse_args()

    print("=" * 150)
    print("EMAIL BROWSER - Extract One at a Time")
    print("=" * 150)

    # Validate agent if provided
    if args.agent and args.agent not in AGENT_EMAILS:
        print(f"\nERROR: Unknown agent email: {args.agent}")
        print("\nAvailable agents:")
        for email, name in AGENT_EMAILS.items():
            print(f"  - {email} ({name})")
        return

    # Get all messages
    messages = list_all_emails(args.agent)

    if not messages:
        print("\nNo emails found!")
        return

    print(f"\nFound {len(messages)} emails")
    print("\nExtracting preview data from all emails...")
    print("(This may take a moment...)\n")

    # Initialize extractor
    extractor = LeadExtractor()

    # Extract preview data from all emails
    previews = []
    for idx, msg in enumerate(messages, 1):
        thread_id = msg.get("threadId")
        progress = f"\rProcessing {idx}/{len(messages)}..."
        print(progress, end="", flush=True)
        preview = extract_preview_data(extractor, thread_id)
        previews.append(preview)

    print("\n")

    # Display table
    display_emails_table(previews)

    # Interactive selection loop
    while True:
        print("\nOptions:")
        print(
            "  - Enter a number (1-{}) to view/process that email".format(
                len(previews)
            )
        )
        print("  - Enter 'r' to refresh the list")
        print("  - Enter 'q' to quit")

        choice = input("\nYour choice: ").strip().lower()

        if choice == 'q':
            print("\nExiting...")
            return

        if choice == 'r':
            # Refresh - re-run the search
            print("\nRefreshing...")
            messages = list_all_emails(args.agent)
            previews = []
            for idx, msg in enumerate(messages, 1):
                thread_id = msg.get("threadId")
                progress = f"\rProcessing {idx}/{len(messages)}..."
                print(progress, end="", flush=True)
                preview = extract_preview_data(extractor, thread_id)
                previews.append(preview)
            print("\n")
            display_emails_table(previews)
            continue

        try:
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(previews):
                selected = previews[choice_idx]

                # Show full details
                print("\n" + "=" * 150)
                print("SELECTED EMAIL - FULL DETAILS")
                print("=" * 150)

                if selected["full_data"]:
                    data = selected["full_data"]

                    print(f"\n{'Field':<25} {'Value'}")
                    print("-" * 150)

                    for key, value in data.items():
                        if value is not None and key not in SKIP_KEYS:
                            if (
                                key == "policy_numbers"
                                and isinstance(value, list)
                            ):
                                print(f"  {key:<23}: {', '.join(value)}")
                            else:
                                print(f"  {key:<23}: {value}")

                    # Show attachments
                    if data.get("attachments"):
                        attachment_count = len(data["attachments"])
                        print(f"\n  Attachments ({attachment_count}):")
                        for att in data["attachments"]:
                            print(f"    - {att['filename']}")

                    print("\n" + "=" * 150)

                    # Ask what to do
                    if data.get("is_duplicate"):
                        duplicate_id = data.get("duplicate_id")
                        warning = (
                            "\nWARNING: This is a duplicate "
                            f"(ID: {duplicate_id})"
                        )
                        print(warning)
                        action = input(
                            "\nSave anyway? [y/N]: "
                        ).strip().upper()
                        if action == "Y":
                            extractor.save_to_supabase(data)
                            print("Saved to Supabase!")
                    else:
                        action = input(
                            "\nSave to Supabase? [Y/n]: "
                        ).strip().upper()
                        if action != "N":
                            extractor.save_to_supabase(data)
                            print("Saved to Supabase!")

                    # Export option
                    export = input("\nExport to CSV? [Y/n]: ").strip().upper()
                    if export != 'N':
                        csv_file = extractor.export_to_csv([data])
                        print(f"Exported to: {csv_file}")
                else:
                    print("\nERROR: Could not extract data from this email")

                print("\n" + "=" * 150)

                # Return to list
                input("\nPress Enter to return to list...")
                display_emails_table(previews)

            else:
                msg_range = (
                    f"\nPlease enter a number between 1 and {len(previews)}"
                )
                print(msg_range)

        except ValueError:
            print("\nInvalid input. Please enter a number, 'r', or 'q'")


if __name__ == '__main__':
    main()
