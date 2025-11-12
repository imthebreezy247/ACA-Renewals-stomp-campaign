# MCP Setup Guide for Gmail Integration

## Overview

This project uses Model Context Protocol (MCP) to interact with Gmail for extracting lead information. The Python script imports wrapper functions from `mcp_functions.py` that need to be connected to an MCP server.

## Prerequisites

1. Python 3.8 or higher
2. Gmail API access
3. MCP server configured for Gmail operations

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `anthropic` - For Claude API access
- `supabase` - For database operations
- `tqdm` - For progress bars
- `google-api-python-client` - For Google Drive (optional)
- `requests` - For Slack notifications (optional)

## Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For Supabase integration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional features
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id  # For attachment uploads
SLACK_WEBHOOK_URL=your_slack_webhook  # For high-value lead alerts
```

## Step 3: MCP Server Configuration

### Option A: Using Claude Desktop with MCP

If you're using Claude Desktop, configure the Gmail MCP server in your Claude configuration:

**Location:**
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gmail"],
      "env": {
        "GMAIL_OAUTH_CLIENT_ID": "your_client_id",
        "GMAIL_OAUTH_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Option B: Standalone MCP Server

If running as a standalone script, you'll need to set up an MCP client that connects to a Gmail MCP server.

**Update `mcp_functions.py`** to use the MCP client:

```python
from anthropic import Anthropic

# Initialize MCP client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def search_gmail_messages(q: str) -> Dict:
    """Search Gmail using MCP"""
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[
            {
                "name": "search_gmail_messages",
                "description": "Search Gmail messages",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "q": {"type": "string", "description": "Gmail search query"}
                    },
                    "required": ["q"]
                }
            }
        ],
        messages=[{
            "role": "user",
            "content": f"Search Gmail with query: {q}"
        }]
    )
    # Process and return response
    return response
```

## Step 4: Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and configure them for MCP

## Step 5: Testing the Setup

Run a test to verify MCP integration:

```python
from mcp_functions import search_gmail_messages

# Test search
result = search_gmail_messages("from:test@example.com")
print(f"Found {len(result.get('messages', []))} messages")
```

## Current Implementation Status

**Current State:** The `mcp_functions.py` file contains stub functions that log warnings when called. These functions return empty data structures to prevent errors.

**To Enable MCP:**
1. Configure MCP server connection (Option A or B above)
2. Update `mcp_functions.py` to use actual MCP client calls
3. Test with sample Gmail queries

## Troubleshooting

### Import Errors

If you see `Import "supabase" could not be resolved`:
```bash
pip install supabase
```

### MCP Connection Errors

If you see warnings about MCP server required:
- Verify MCP server is running
- Check environment variables are set
- Ensure Gmail API credentials are valid

### Gmail Authentication

If Gmail API calls fail:
- Regenerate OAuth tokens
- Check API quotas in Google Cloud Console
- Verify scopes include Gmail read access

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
