# Setup Instructions

## 1. Environment Configuration ✅

Your `.env` file has been configured with:
- ✅ Anthropic API Key
- ✅ Supabase URL: `https://delgvqjilrzjigdovxao.supabase.co`
- ✅ Supabase Service Role Key (for backend operations)
- ✅ Database connection string (for direct SQL access)

## 2. Create Database Tables

### Option A: Using Supabase Dashboard (Recommended)

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/editor

2. **Run the Schema:**
   - Open the file `supabase_schema.sql` in this directory
   - Copy all the SQL code
   - Paste it into the Supabase SQL Editor
   - Click "Run" or press Ctrl+Enter

3. **Verify Tables Created:**
   - Go to: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/editor
   - You should see two new tables:
     - `leads` - Main table for client information
     - `attachments` - Table for email attachments

### Option B: Using Command Line (Alternative)

If you have `psql` installed:

```bash
# Load environment variables
source .env  # Linux/Mac
# or
set -a; source .env; set +a  # Alternative

# Run SQL file
psql "$SUPABASE_DB_URL" -f supabase_schema.sql
```

## 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `anthropic` - Claude API client
- `supabase` - Supabase Python client
- `tqdm` - Progress bars
- `python-dotenv` - Environment variable management

Optional packages:
- `google-api-python-client` - For Google Drive uploads
- `requests` - For Slack notifications

## 4. Configure Supabase MCP (Optional)

### For VS Code:

Create or update `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=delgvqjilrzjigdovxao"
    }
  }
}
```

This allows you to interact with Supabase through the MCP protocol in VS Code.

## 5. Test the Setup

### Test Database Connection:

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Test query
result = supabase.table('leads').select('count').limit(1).execute()
print("✅ Database connection successful!")
```

### Test the Extraction Script:

```bash
# Dry run (no actual Gmail access until MCP configured)
python extract_all_deals-properly-mcp.py --max 5
```

## 6. Database Schema Overview

### `leads` Table
Stores extracted client information:
- `id` - UUID primary key
- `client_name`, `client_phone`, `client_email` - Contact info
- `monthly_premium`, `aca_premium` - Premium amounts
- `annual_income` - Client's annual income
- `referring_agent` - Which agent sent the referral
- `thread_id` - Gmail thread ID (unique)
- `confidence` - Extraction confidence (high/medium/low)
- `status` - Processing status
- `is_duplicate` - Duplicate flag
- Timestamps: `extracted_at`, `created_at`, `updated_at`

### `attachments` Table
Stores email attachment metadata:
- `id` - UUID primary key
- `lead_id` - Foreign key to leads table
- `filename`, `mime_type` - File information
- `local_path` - Path to downloaded file
- `attachment_id`, `message_id` - Gmail IDs

## 7. Verify Setup

Run this checklist:

- [ ] `.env` file has all required environment variables
- [ ] Database tables created in Supabase
- [ ] Python dependencies installed (`pip list | grep supabase`)
- [ ] MCP configuration added to VS Code (optional)
- [ ] Test connection works

## Security Notes

⚠️ **IMPORTANT:**
- Your `.env` file contains sensitive credentials
- Never commit `.env` to version control
- The `.gitignore` file should include `.env`
- The service_role key bypasses Row Level Security - use carefully
- Consider rotating keys if they've been exposed

## Troubleshooting

### "Table does not exist" error
- Run the SQL schema in Supabase SQL Editor
- Check that you're connected to the correct project

### Import errors
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### MCP connection issues
- Verify Supabase URL in `.env`
- Check API key is valid
- Review MCP_SETUP_GUIDE.md for Gmail MCP setup

## Next Steps

Once setup is complete:
1. Configure Gmail MCP server (see MCP_SETUP_GUIDE.md)
2. Test with a small batch of emails
3. Review extracted data in Supabase dashboard
4. Set up optional integrations (Google Drive, Slack)

## Support

- Supabase Dashboard: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao
- Supabase Docs: https://supabase.com/docs
- Project Issues: Review ERROR_FIXES_SUMMARY.md for common issues
