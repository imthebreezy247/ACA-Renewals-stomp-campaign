"""
Gmail API helper functions used by the lead extraction pipeline.
Handles OAuth authentication, message search, thread fetching, and attachment downloads.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
_TOKEN_PATH = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))
_CREDENTIALS_PATH = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
_MAX_RESULTS_DEFAULT = int(os.getenv("GMAIL_MAX_RESULTS", "500"))
_gmail_service = None


def _load_credentials() -> Credentials:
    """Load OAuth credentials, prompting the user if necessary."""
    creds: Optional[Credentials] = None

    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing Gmail token...")
            creds.refresh(Request())
        else:
            if not _CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {_CREDENTIALS_PATH}. "
                    "Download OAuth client credentials from Google Cloud Console."
                )

            logger.info("Launching Gmail OAuth consent flow...")
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_PATH), SCOPES)
            port = int(os.getenv("GMAIL_OAUTH_PORT", "0") or 0)

            try:
                creds = flow.run_local_server(port=port)
            except OSError:
                # Fall back to console auth in headless environments
                creds = flow.run_console()

        _TOKEN_PATH.write_text(creds.to_json())
        logger.info(f"Saved refreshed Gmail token to {_TOKEN_PATH}")

    return creds


def _get_gmail_service():
    """Return a cached Gmail API service instance."""
    global _gmail_service

    if _gmail_service is None:
        creds = _load_credentials()
        _gmail_service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service initialized")

    return _gmail_service


def search_gmail_messages(q: str, max_results: Optional[int] = None) -> Dict[str, Any]:
    """
    Search Gmail using the REST API.

    Args:
        q: Gmail search query string
        max_results: Optional cap on number of messages to return

    Returns:
        Dict containing 'messages' and 'resultSizeEstimate'
    """
    service = _get_gmail_service()
    collected = []
    page_token = None
    target = max_results or _MAX_RESULTS_DEFAULT

    try:
        while True:
            remaining = max(1, min(500, target - len(collected)))
            request = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=q,
                    maxResults=remaining,
                    pageToken=page_token,
                )
            )
            response = request.execute()

            collected.extend(response.get("messages", []))
            page_token = response.get("nextPageToken")

            if not page_token or len(collected) >= target:
                break

        logger.info("Gmail search '%s' returned %d messages", q, len(collected))
        return {"messages": collected[:target], "resultSizeEstimate": len(collected)}

    except HttpError as exc:
        logger.error("Gmail search failed: %s", exc)
        return {"messages": [], "error": str(exc)}


def read_gmail_thread(thread_id: str, include_full_messages: bool = True) -> Dict[str, Any]:
    """
    Fetch a Gmail thread, optionally including full message payloads.

    Args:
        thread_id: Gmail thread ID
        include_full_messages: Whether to include full bodies/headers

    Returns:
        Thread resource dict
    """
    service = _get_gmail_service()
    fmt = "full" if include_full_messages else "metadata"

    try:
        thread = (
            service.users()
            .threads()
            .get(userId="me", id=thread_id, format=fmt)
            .execute()
        )
        return thread
    except HttpError as exc:
        logger.error("Failed to read thread %s: %s", thread_id, exc)
        return {"messages": [], "threadId": thread_id, "error": str(exc)}


def download_attachment(message_id: str, attachment_id: str, save_path: str) -> bool:
    """
    Download a Gmail attachment to the local filesystem.

    Args:
        message_id: Gmail message ID
        attachment_id: Attachment ID
        save_path: Local path for saved file

    Returns:
        bool: True on success
    """
    service = _get_gmail_service()

    try:
        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = attachment.get("data")
        if not data:
            logger.warning(
                "Attachment %s on message %s had no data payload", attachment_id, message_id
            )
            return False

        file_bytes = base64.urlsafe_b64decode(data.encode("utf-8"))
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file_bytes)
        return True

    except HttpError as exc:
        logger.error(
            "Failed to download attachment %s from message %s: %s",
            attachment_id,
            message_id,
            exc,
        )
        return False
