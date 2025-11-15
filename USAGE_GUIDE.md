# ACA Lead Extraction - Usage Guide

## Quick Start

### Extract One Email at a Time (Interactive)
```bash
python extract_single_email.py
```
This interactive script will:
- Show you a list of available emails
- Let you pick which one to extract
- Preview the email before processing
- Show extraction results
- Ask if you want to save to Supabase
- Ask if you want to export to CSV

### Extract Multiple Emails (Batch Mode)

**Process 5 emails:**
```bash
python extract_all_deals-properly-mcp.py --max 5
```

**Process 1 email:**
```bash
python extract_all_deals-properly-mcp.py --max 1
```

**Process specific agent's emails:**
```bash
python extract_all_deals-properly-mcp.py --agent danielberman.ushealth@gmail.com --max 5
```

**Auto-save high-confidence leads:**
```bash
python extract_all_deals-properly-mcp.py --max 10 --auto-save
```

**Filter by date:**
```bash
python extract_all_deals-properly-mcp.py --after 2024/01/01 --max 20
```

## Setup Required

### 1. Environment Variables

Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Then edit `.env` and add:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

Get these from:
- **Supabase**: https://app.supabase.com → Project Settings → API
- **Anthropic**: https://console.anthropic.com → API Keys

### 2. Create Supabase Tables

Run the SQL in your Supabase SQL Editor:
```bash
# Copy the content of supabase_schema.sql
# Paste into: https://app.supabase.com → SQL Editor → New Query
```

## IDE Warnings (Can be Ignored)

### Pylance Import Warnings
The warnings about `anthropic` and `supabase` imports are just IDE warnings. The packages are installed and work correctly when you run the script.

### SQL Syntax Warnings
The `supabase_schema.sql` file shows errors because VS Code's MSSQL extension is trying to parse PostgreSQL syntax. The SQL file is correct for Supabase! These warnings are now suppressed with the `.vscode/settings.json` configuration.

## Troubleshooting

### "Could not resolve authentication method"
Make sure your `.env` file has the correct Supabase credentials:
```bash
# Check if .env file exists
ls -la .env

# Make sure it contains:
# SUPABASE_URL=...
# SUPABASE_KEY=...
# ANTHROPIC_API_KEY=...
```

### "No messages found"
Make sure:
1. You have emails with attachments from the configured agents
2. The emails have the correct Gmail labels
3. You're authenticated with Gmail (check `token.json` exists)

## Command Line Options

```
--agent EMAIL      Filter by specific agent email
--after DATE       Filter by date (YYYY/MM/DD)
--max NUMBER       Maximum emails to process (default: 100)
--auto-save        Auto-save high confidence leads to Supabase
--no-csv           Skip CSV export
```

## Examples

**Extract 1 email from Daniel Berman:**
```bash
python extract_all_deals-properly-mcp.py --agent danielberman.ushealth@gmail.com --max 1
```

**Extract emails from last week:**
```bash
python extract_all_deals-properly-mcp.py --after 2024/11/07 --max 10
```

**Batch process and auto-save:**
```bash
python extract_all_deals-properly-mcp.py --max 50 --auto-save
```

**Interactive single email:**
```bash
python extract_single_email.py
```
