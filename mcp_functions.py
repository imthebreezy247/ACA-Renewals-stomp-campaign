"""
MCP Tool Wrapper Functions for Gmail operations.
These functions should be imported into the main extraction script.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def search_gmail_messages(q: str) -> Dict:
    """
    Wrapper for Gmail MCP search tool.
    This should be called via MCP server. For now, returns mock data.
    Configure MCP server connection in your environment.

    Args:
        q: Gmail search query string

    Returns:
        Dict with 'messages' list
    """
    logger.warning("⚠️  search_gmail_messages called - MCP server required")
    logger.warning("⚠️  Please configure Gmail MCP server to use this functionality")
    logger.info(f"Search query: {q}")
    # In production, this would use MCP client to call the actual tool
    # For now, return empty structure to prevent errors
    return {"messages": []}


def read_gmail_thread(thread_id: str, include_full_messages: bool = True) -> Dict:
    """
    Wrapper for Gmail MCP thread reader.
    This should be called via MCP server. For now, returns mock data.

    Args:
        thread_id: Gmail thread ID
        include_full_messages: Whether to include full message bodies

    Returns:
        Dict with 'messages' list and 'threadId'
    """
    logger.warning(f"⚠️  read_gmail_thread called for {thread_id} - MCP server required")
    logger.warning("⚠️  Please configure Gmail MCP server to use this functionality")
    return {"messages": [], "threadId": thread_id}


def download_attachment(message_id: str, attachment_id: str, save_path: str) -> bool:
    """
    Wrapper for Gmail MCP attachment downloader.
    This should be called via MCP server. For now, returns False.

    Args:
        message_id: Gmail message ID
        attachment_id: Attachment ID
        save_path: Local path to save attachment

    Returns:
        bool: Success status
    """
    logger.warning(f"⚠️  download_attachment called - MCP server required")
    logger.warning(f"⚠️  Would save to: {save_path}")
    logger.warning("⚠️  Please configure Gmail MCP server to use this functionality")
    return False
