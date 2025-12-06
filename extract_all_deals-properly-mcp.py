#!/usr/bin/env python3
"""
ACA Lead Extraction System - Production Version
Features: Gmail search, attachment extraction, Google Drive upload, Slack alerts, 
duplicate detection, CSV export, web dashboard
"""

import json
import os
import re
import time
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from html import unescape
from anthropic import Anthropic
from tqdm import tqdm
import logging
import csv
from io import StringIO
from dotenv import load_dotenv
# Import MCP wrapper functions
from mcp_functions import search_gmail_messages, read_gmail_thread, download_attachment

# Load environment variables from .env file
load_dotenv()

# Configuration
CONFIG = {
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
    'supabase_url': os.getenv('SUPABASE_URL'),
    'supabase_key': os.getenv('SUPABASE_KEY'),
    'google_drive_folder_id': os.getenv('GOOGLE_DRIVE_FOLDER_ID'),  # Optional
    'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),  # Optional
    'attachments_dir': './attachments',
    'log_file': './extraction.log',
    'csv_export_dir': './exports',
    'batch_size': 10,
    'high_value_threshold': 200.00,  # Premium amount for Slack notification
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Agent email mappings
AGENT_EMAILS = {
    'danielberman.ushealth@gmail.com': 'Daniel Berman',
    'jordang.ushealth@gmail.com': 'Jordan Gassner',
    'richardodle.ushealth@gmail.com': 'Richard Odle',
    'carlosvarona.ushealth@gmail.com': 'Carlos Varona',
    'miguelgarcia.unitedhealth@gmail.com': 'Miguel Garcia',
    'charlie.ushealth@gmail.com': 'Charlie Rios',
    'nick.unitedhealth@gmail.com': 'Nick Salamanca'
}

# Blocked values - FIXED
BLOCKED_NAMES = [
    'christopher shannahan', 'chris shannahan', 'tanya centore', 'sevy',
    'daniel berman', 'jordan gassner', 'richard odle', 'carlos varona',
    'miguel garcia', 'charlie rios', 'nick salamanca', 'nicolas salamanca',
    'health advisor', 'insurance agent', 'writing agent'
]

# Only block YOUR company domains from client_email field
BLOCKED_CLIENT_EMAIL_DOMAINS = [
    '@cjsinsurancesolutions.com',
    '@tdcempoweredhealth.com'
]

# Gmail label configuration
DEFAULT_INCLUDED_LABELS = [
    'processed-sold-deals-using-automation-to-final-label',
    'sold-deal',
    'aca-leads-to-be-worked-working-deal',
    'aca-leads-to-be-worked-working-deal-2nd-attempt',
    'aca-leads-to-be-worked-working-deal-3rd-attempt',
    'sold-deal-paid---sold-deals',
    'ron-deals--aca',
]

EXCLUDED_LABELS = [
    'aca-leads-to-be-worked-dead-deal',
    'all-wraps-to-be-worked'  # explicitly exclude noisy bulk wrap label by default
]


class LeadExtractor:
    """Main class for extracting leads from Gmail with all features"""

    # Minimum seconds between Claude API calls to stay under rate limits
    # With 30k tokens/min limit and ~15-20k tokens per request, need ~45-60s between calls
    MIN_API_CALL_INTERVAL = 60

    def __init__(self):
        # Configure Anthropic client - disable automatic retries so we can handle rate limits properly
        self.anthropic = Anthropic(
            api_key=CONFIG['anthropic_api_key'],
            max_retries=0,  # Disable SDK retries - we handle rate limits ourselves
        )
        self.attachments_dir = Path(CONFIG['attachments_dir'])
        self.attachments_dir.mkdir(exist_ok=True)
        self.csv_export_dir = Path(CONFIG['csv_export_dir'])
        self.csv_export_dir.mkdir(exist_ok=True)
        self._last_api_call = 0  # Track last API call timestamp
        logger.info("LeadExtractor initialized")

    def _wait_for_rate_limit(self):
        """Enforce minimum interval between Claude API calls to respect rate limits"""
        elapsed = time.time() - self._last_api_call
        if elapsed < self.MIN_API_CALL_INTERVAL:
            wait_time = self.MIN_API_CALL_INTERVAL - elapsed
            logger.info(f"Rate limit: waiting {wait_time:.1f}s before next API call...")
            time.sleep(wait_time)
        self._last_api_call = time.time()

    def search_agent_emails(self, 
                           agent_email: Optional[str] = None,
                           after_date: Optional[str] = None,
                           before_date: Optional[str] = None,
                           max_results: int = 100,
                           included_labels: Optional[List[str]] = None,
                           allow_drive: bool = False,
                           ignore_default_excludes: bool = False) -> List[Dict]:
        """
        Search Gmail for agent referral emails with label filtering
        
        Args:
            agent_email: Specific agent to search (optional)
            after_date: Date filter YYYY/MM/DD (optional)
            max_results: Max results to return
            
        Returns:
            List of message metadata
        """
        logger.info(f"Searching Gmail: agent={agent_email}, after={after_date}")
        
        # Build search query
        query_parts = []
        
        if agent_email:
            query_parts.append(f"from:{agent_email}")
        else:
            # Search all known agents
            agent_queries = [f"from:{email}" for email in AGENT_EMAILS.keys()]
            query_parts.append(f"({' OR '.join(agent_queries)})")
        
        if after_date:
            query_parts.append(f"after:{after_date}")
        if before_date:
            query_parts.append(f"before:{before_date}")
        
        # Include specific labels (OR logic)
        labels_to_use = included_labels or DEFAULT_INCLUDED_LABELS
        label_queries = [f"label:{label}" for label in labels_to_use]
        query_parts.append(f"({' OR '.join(label_queries)})")
        
        # Exclude dead deals
        if not ignore_default_excludes:
            for excluded in EXCLUDED_LABELS:
                query_parts.append(f"-label:{excluded}")
        
        # Filter for attachments
        if allow_drive:
            query_parts.append("(has:attachment OR has:drive)")
        else:
            query_parts.append("has:attachment")
        
        query = " ".join(query_parts)
        logger.info(f"Gmail query: {query}")
        
        # Execute search using Gmail MCP
        results = search_gmail_messages(q=query, max_results=max_results)
        
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} messages")
        
        return messages[:max_results]
    
    def check_duplicate(self, client_phone: str, thread_id: str) -> Optional[Dict]:
        """
        Check if lead already exists in Supabase
        
        Args:
            client_phone: Phone number to check
            thread_id: Gmail thread ID
            
        Returns:
            Existing lead data if found, None otherwise
        """
        try:
            from supabase import create_client
            supabase = create_client(CONFIG['supabase_url'], CONFIG['supabase_key'])
            
            # Check by phone
            result = supabase.table('leads').select('*').eq('client_phone', client_phone).execute()
            
            if result.data:
                logger.warning(f"WARNING: Duplicate found: {client_phone}")
                return result.data[0]
            
            # Check by thread_id
            result = supabase.table('leads').select('*').eq('thread_id', thread_id).execute()
            
            if result.data:
                logger.warning(f"WARNING: Thread already processed: {thread_id}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return None
    
    def get_processed_thread_ids(self) -> set:
        """Get all thread_ids that have already been processed from Supabase"""
        try:
            from supabase import create_client
            supabase = create_client(CONFIG['supabase_url'], CONFIG['supabase_key'])

            result = supabase.table('leads').select('thread_id').execute()
            thread_ids = {row['thread_id'] for row in result.data if row.get('thread_id')}
            logger.info(f"Found {len(thread_ids)} already-processed threads in database")
            return thread_ids
        except Exception as e:
            logger.error(f"Failed to get processed threads: {e}")
            return set()

    def _get_header_value(self, message: Dict, name: str) -> Optional[str]:
        """Helper to fetch a header value from a Gmail message."""
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == name.lower():
                return header.get('value')
        return None

    def _decode_message_text(self, payload: Dict, max_chars: int = 4000) -> Optional[str]:
        """
        Decode text parts from a Gmail message payload and return a truncated plain-text body.
        """
        texts: List[str] = []

        def walk(part: Dict):
            if not part:
                return
            mime_type = part.get('mimeType', '')
            body = part.get('body', {})
            data = body.get('data')
            if data and mime_type.startswith('text/'):
                try:
                    decoded = base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')
                    if mime_type == 'text/html':
                        decoded = re.sub(r'<[^>]+>', ' ', decoded)
                    decoded = unescape(decoded)
                    texts.append(decoded)
                except Exception:
                    pass
            for child in part.get('parts') or []:
                walk(child)

        walk(payload)
        combined = "\n".join(texts).strip()
        if not combined:
            return None
        combined = re.sub(r'\s+', ' ', combined)
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "...(truncated)"
        return combined

    def _build_thread_summary(self, thread: Dict, max_messages: int = 2, body_limit: int = 1200) -> List[Dict[str, Any]]:
        """
        Build a trimmed thread summary for the model (avoid full raw payloads to reduce token bloat).
        Includes headers, snippet, and truncated plain-text body per message.
        """
        summary = []
        messages = thread.get('messages', [])
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        for msg in messages:
            payload = msg.get('payload', {})
            summary.append({
                'id': msg.get('id'),
                'threadId': msg.get('threadId'),
                'from': self._get_header_value(msg, 'from'),
                'to': self._get_header_value(msg, 'to'),
                'subject': self._get_header_value(msg, 'subject'),
                'date': self._get_header_value(msg, 'date'),
                'snippet': msg.get('snippet'),
                'body': self._decode_message_text(payload, max_chars=body_limit)
            })
        return summary

    def extract_client_from_thread(self, thread_id: str, preloaded_thread: Optional[Dict] = None, agent_email: Optional[str] = None) -> Dict[str, Any]:
        """Extract client data from Gmail thread"""
        logger.info(f"Extracting from thread: {thread_id}")
        
        # Check duplicate first
        # Note: We'll check again after extraction when we have the phone number
        
        # Read full thread
        thread = preloaded_thread or read_gmail_thread(
            thread_id=thread_id,
            include_full_messages=True
        )
        
        # Extract client data using Claude
        client_data = self._extract_with_claude(thread, thread_id)

        # Ensure referring agent is set (prefer extraction, fallback to provided agent_email)
        if agent_email and not client_data.get('referring_agent'):
            client_data['referring_agent'] = AGENT_EMAILS.get(agent_email, agent_email)
        
        # Check duplicate by phone
        if client_data.get('client_phone'):
            duplicate = self.check_duplicate(client_data['client_phone'], thread_id)
            if duplicate:
                client_data['is_duplicate'] = True
                client_data['duplicate_id'] = duplicate.get('id')
                logger.warning(f"Duplicate detected: {client_data['client_name']}")
        
        # Extract attachments
        attachments = self._extract_attachments(thread, thread_id)
        client_data['attachments'] = attachments
        
        # Upload to Google Drive (if configured)
        if CONFIG.get('google_drive_folder_id') and attachments:
            client_data['drive_folder_url'] = self._upload_to_drive(attachments, thread_id)
        
        # Clean and validate
        client_data = self._clean_extraction(client_data)
        
        # Send Slack notification for high-value leads (handle missing premiums safely)
        monthly_premium = client_data.get('monthly_premium')
        try:
            monthly_value = float(monthly_premium) if monthly_premium is not None else 0.0
        except (TypeError, ValueError):
            monthly_value = 0.0

        if monthly_value >= CONFIG['high_value_threshold'] and not client_data.get('is_duplicate'):
            self._send_slack_notification(client_data)
        
        logger.info(f"Extracted: {client_data.get('client_name', 'Unknown')}")
        return client_data
    
    def _truncate_thread_for_claude(self, thread: Dict) -> str:
        """
        Build a trimmed thread summary string for the model to prevent huge prompts.
        Keeps only headers/snippet/body (plain text) for the most recent messages.
        """
        # Start aggressively small
        summary = self._build_thread_summary(thread, max_messages=2, body_limit=1200)
        summary_json = json.dumps(summary, indent=2)

        # If still large, shrink to a single message
        if len(summary_json) > 12000:
            summary = self._build_thread_summary(thread, max_messages=1, body_limit=800)
            summary_json = json.dumps(summary, indent=2)
        if len(summary_json) > 12000:
            logger.warning(f"Thread too large ({len(summary_json)} chars) even after trimming; truncating string for prompt.")
            summary_json = summary_json[:12000] + "...(truncated)"

        return summary_json

    def _extract_with_claude(self, thread: Dict, thread_id: str) -> Dict:
        """Use Claude to extract structured client data"""

        # Truncate thread to avoid token limit errors
        truncated_thread = self._truncate_thread_for_claude(thread)

        prompt = f"""
Extract CLIENT information from this agent referral email.

RECOGNIZED AGENT FORMATS (7 total):

**Daniel Berman (danielberman.ushealth@gmail.com):**
- "Monthly Premium: $XXX.XX", app number, email, phone

**Jordan Gassner (jordang.ushealth@gmail.com):**
- Subject "ACA Signup", simple format with income

**Richard Odle (richardodle.ushealth@gmail.com):**
- Subject "[Name] ACA", informal notes

**Carlos Varona (carlosvarona.ushealth@gmail.com):**
- Demographics format, "Premium: $XX"

**Miguel Garcia (miguelgarcia.unitedhealth@gmail.com):**
- Subject "[Name] - ACA wrap", multiple phones, dual premiums

**Charlie Rios (charlie.ushealth@gmail.com):**
- Subject "[Name] (Phone)", APPLICATION SUMMARY

**Nick Salamanca (nick.unitedhealth@gmail.com):**
- "Quoted on [Plan] for $X/month. Total quoted monthly was $XX.XX"

EXTRACT PRIMARY CLIENT DATA:
1. client_name: Full name (NOT agent/spouse unless primary)
2. client_phone: Phone (xxx-xxx-xxxx format)
3. client_email: Email if present
4. monthly_premium: Total recurring monthly cost
5. aca_premium: ACA marketplace premium if mentioned
6. annual_income: Income (convert "20k" to 20000)
7. referring_agent: Agent name (Daniel Berman, Jordan Gassner, etc.)
8. application_number: App/control number if present
9. policy_numbers: Array of policy numbers if present
10. household_size: Number in household
11. zip_code: Zip code if mentioned
12. date_of_birth: Client DOB if mentioned (YYYY-MM-DD format)
13. dependents: Spouse/children info if mentioned
14. contact_notes: Any special contact instructions

CRITICAL RULES:
- NEVER extract Christopher Shannahan, Tanya Centore, Sevy as client
- NEVER extract @cjsinsurancesolutions.com or @tdcempoweredhealth.com as client email
- If client_email matches any agent email exactly, set to null
- Agent is the SENDER, not the client
- For families, extract PRIMARY applicant (usually first mentioned adult)

EMAIL THREAD:
{truncated_thread}

Return ONLY valid JSON:
{{
  "client_name": "",
  "client_phone": "",
  "client_email": null,
  "monthly_premium": null,
  "aca_premium": null,
  "annual_income": null,
  "referring_agent": "",
  "application_number": null,
  "policy_numbers": null,
  "household_size": null,
  "zip_code": null,
  "date_of_birth": null,
  "dependents": null,
  "contact_notes": null,
  "thread_id": "{thread_id}",
  "confidence": "high|medium|low"
}}

Use null for missing fields.
"""

        # Retry logic for rate limits (max 3 attempts)
        max_retries = 3
        for attempt in range(max_retries):
            # Wait for rate limit before making API call
            self._wait_for_rate_limit()

            try:
                response = self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'rate_limit' in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 65 * (attempt + 1)  # 65s, 130s, 195s
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        self._last_api_call = 0  # Reset timer to force wait
                        continue
                raise  # Re-raise if not rate limit or max retries reached

        # Extract JSON from response (handle markdown code blocks)
        response_text = response.content[0].text.strip()

        # Try to extract JSON from markdown code blocks
        if '```json' in response_text:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        elif '```' in response_text:
            json_match = re.search(r'```\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

        # Parse JSON
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            raise
    
    def _extract_attachments(self, thread: Dict, thread_id: str) -> List[Dict]:
        """Extract and download all attachments from thread"""
        attachments = []
        
        # Create thread-specific directory
        thread_dir = self.attachments_dir / thread_id
        thread_dir.mkdir(exist_ok=True)
        
        # Parse thread for attachments
        messages = thread.get('messages', [])
        
        for msg in messages:
            msg_id = msg.get('id', '')
            parts = msg.get('payload', {}).get('parts', [])
            
            for part in parts:
                if part.get('filename'):
                    attachment_id = part.get('body', {}).get('attachmentId')
                    filename = part.get('filename')
                    mime_type = part.get('mimeType', '')
                    
                    if attachment_id:
                        try:
                            local_path = thread_dir / filename
                            
                            # Download using Gmail MCP
                            download_attachment(
                                message_id=msg_id,
                                attachment_id=attachment_id,
                                save_path=str(local_path)
                            )
                            
                            attachments.append({
                                'filename': filename,
                                'mime_type': mime_type,
                                'local_path': str(local_path),
                                'attachment_id': attachment_id,
                                'message_id': msg_id
                            })
                            
                            logger.info(f"Downloaded: {filename}")
                            
                        except Exception as e:
                            logger.error(f"Failed to download {filename}: {e}")
        
        return attachments
    
    def _upload_to_drive(self, attachments: List[Dict], thread_id: str) -> str:
        """
        Upload attachments to Google Drive
        
        Args:
            attachments: List of attachment metadata
            thread_id: Gmail thread ID (used for folder name)
            
        Returns:
            Google Drive folder URL
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials
            
            # Initialize Drive API
            creds = Credentials.from_authorized_user_file('token.json')
            service = build('drive', 'v3', credentials=creds)
            
            # Create folder for this lead
            folder_metadata = {
                'name': f'Lead_{thread_id}',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [CONFIG['google_drive_folder_id']]
            }
            folder = service.files().create(body=folder_metadata, fields='id,webViewLink').execute()
            folder_id = folder['id']
            folder_url = folder['webViewLink']
            
            # Upload each attachment
            for attachment in attachments:
                file_metadata = {
                    'name': attachment['filename'],
                    'parents': [folder_id]
                }
                media = MediaFileUpload(
                    attachment['local_path'],
                    mimetype=attachment['mime_type']
                )
                service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                logger.info(f"Uploaded to Drive: {attachment['filename']}")
            
            return folder_url
            
        except Exception as e:
            logger.error(f"Failed to upload to Drive: {e}")
            return None
    
    def _send_slack_notification(self, data: Dict):
        """
        Send Slack notification for high-value leads
        
        Args:
            data: Extracted client data
        """
        if not CONFIG.get('slack_webhook_url'):
            return
        
        try:
            import requests
            
            premium = data.get('monthly_premium', 0)
            
            message = {
                "text": f"🎯 High-Value Lead Extracted!",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"💰 ${premium:.2f}/mo - {data.get('client_name', 'Unknown')}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Phone:*\n{data.get('client_phone', 'N/A')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Email:*\n{data.get('client_email', 'N/A')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Income:*\n${data.get('annual_income', 0):,}/year"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Agent:*\n{data.get('referring_agent', 'N/A')}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Attachments:* {len(data.get('attachments', []))} files"
                        }
                    }
                ]
            }
            
            if data.get('drive_folder_url'):
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{data['drive_folder_url']}|View in Google Drive>"
                    }
                })
            
            requests.post(CONFIG['slack_webhook_url'], json=message)
            logger.info("Slack notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def _clean_extraction(self, data: Dict) -> Dict:
        """Clean and validate extracted data - FIXED email blocking logic"""
        
        # Lowercase email
        if data.get('client_email'):
            data['client_email'] = data['client_email'].lower()
            
            # Block YOUR company domains only
            if any(domain in data['client_email'] for domain in BLOCKED_CLIENT_EMAIL_DOMAINS):
                data['client_email'] = None
                data['confidence'] = 'low'
            
            # Block if it exactly matches any agent email
            if data['client_email'] in AGENT_EMAILS.keys():
                data['client_email'] = None
                data['confidence'] = 'low'
        
        # Standardize phone
        if data.get('client_phone'):
            digits = re.sub(r'\D', '', data['client_phone'])
            if len(digits) == 10:
                data['client_phone'] = f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                data['client_phone'] = f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            else:
                data['client_phone'] = None
                data['confidence'] = 'low'
        
        # Clean premiums
        for field in ['monthly_premium', 'aca_premium', 'initiation_fee']:
            if data.get(field):
                if isinstance(data[field], str):
                    clean = data[field].replace('$', '').replace(',', '').replace('/month', '')
                    try:
                        data[field] = float(clean)
                    except:
                        data[field] = None
        
        # Clean income
        if data.get('annual_income'):
            if isinstance(data['annual_income'], str):
                clean = data['annual_income'].replace('$', '').replace(',', '').replace('/year', '')
                clean = clean.replace('k', '000').replace('K', '000')
                try:
                    data['annual_income'] = int(float(clean))
                except:
                    data['annual_income'] = None
        
        # Block agent names in client_name
        if data.get('client_name'):
            name_lower = data['client_name'].lower()
            if any(blocked in name_lower for blocked in BLOCKED_NAMES):
                data['client_name'] = None
                data['confidence'] = 'low'
        
        # Ensure referring_agent is never Chris/Tanya
        if data.get('referring_agent'):
            agent_lower = data['referring_agent'].lower()
            if agent_lower in ['christopher shannahan', 'chris shannahan', 'tanya centore', 'sevy']:
                data['referring_agent'] = None
        
        # Add extraction timestamp
        data['extracted_at'] = datetime.utcnow().isoformat()
        
        return data
    
    def save_to_supabase(self, data: Dict) -> bool:
        """Save extracted lead to Supabase"""

        # Check required fields before attempting to save
        required_fields = ['client_name', 'client_phone']
        missing = [f for f in required_fields if not data.get(f)]

        if missing:
            logger.warning(f"Skipping save - missing required fields: {missing} for lead: {data.get('client_name', 'Unknown')}")
            return False

        try:
            from supabase import create_client

            supabase = create_client(CONFIG['supabase_url'], CONFIG['supabase_key'])
            
            # Prepare data for insert
            lead_data = {
                'client_name': data.get('client_name'),
                'client_phone': data.get('client_phone'),
                'client_email': data.get('client_email'),
                'monthly_premium': data.get('monthly_premium'),
                'aca_premium': data.get('aca_premium'),
                'annual_income': data.get('annual_income'),
                'referring_agent': data.get('referring_agent'),
                'application_number': data.get('application_number'),
                'policy_numbers': data.get('policy_numbers'),
                'household_size': data.get('household_size'),
                'zip_code': data.get('zip_code'),
                'date_of_birth': data.get('date_of_birth'),
                'dependents': data.get('dependents'),
                'contact_notes': data.get('contact_notes'),
                'thread_id': data.get('thread_id'),
                'confidence': data.get('confidence'),
                'drive_folder_url': data.get('drive_folder_url'),
                'extracted_at': data.get('extracted_at'),
                'is_duplicate': data.get('is_duplicate', False),
                'status': 'pending_review' if data.get('confidence') != 'high' else 'ready_to_contact'
            }
            
            # Insert lead
            result = supabase.table('leads').insert(lead_data).execute()
            lead_id = result.data[0]['id']
            
            # Insert attachments
            for attachment in data.get('attachments', []):
                attachment_data = {
                    'lead_id': lead_id,
                    'filename': attachment['filename'],
                    'mime_type': attachment['mime_type'],
                    'local_path': attachment['local_path'],
                    'attachment_id': attachment['attachment_id'],
                    'message_id': attachment['message_id']
                }
                supabase.table('attachments').insert(attachment_data).execute()
            
            logger.info(f"Saved to Supabase: {data['client_name']} (ID: {lead_id})")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Failed to save to Supabase: {e}")
            return False
    
    def export_to_csv(self, leads: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export leads to CSV file
        
        Args:
            leads: List of extracted leads
            filename: Optional custom filename
            
        Returns:
            Path to CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"leads_export_{timestamp}.csv"
        
        filepath = self.csv_export_dir / filename
        
        # Define CSV columns
        fieldnames = [
            'client_name', 'client_phone', 'client_email', 
            'monthly_premium', 'aca_premium', 'annual_income',
            'referring_agent', 'application_number', 'household_size',
            'zip_code', 'date_of_birth', 'dependents', 'contact_notes',
            'thread_id', 'confidence', 'is_duplicate', 'extracted_at'
        ]
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for lead in leads:
                # Convert lists to strings for CSV
                if lead.get('policy_numbers'):
                    lead['policy_numbers_str'] = ', '.join(lead['policy_numbers'])
                writer.writerow(lead)
        
        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return str(filepath)
    
    def process_batch(self, 
                     agent_email: Optional[str] = None,
                     after_date: Optional[str] = None,
                     before_date: Optional[str] = None,
                     max_results: int = 100,
                     auto_save: bool = False,
                     export_csv: bool = True,
                     report_only: bool = False,
                     included_labels: Optional[List[str]] = None,
                     skip_multi_message_threads: bool = False,
                     allow_drive: bool = False,
                     ignore_default_excludes: bool = False) -> List[Dict]:
        """
        Process a batch of emails with all features
        
        Args:
            agent_email: Filter by agent
            after_date: Filter by date
            max_results: Max emails to process
            auto_save: Auto-save to Supabase without review
            export_csv: Export results to CSV
            
        Returns:
            List of extracted leads
        """
        # Search emails
        messages = self.search_agent_emails(
            agent_email,
            after_date,
            before_date,
            max_results,
            included_labels,
            allow_drive,
            ignore_default_excludes
        )

        if not messages:
            logger.info("No messages found")
            return []

        # Filter out already-processed threads
        processed_threads = self.get_processed_thread_ids()
        original_count = len(messages)
        messages = [msg for msg in messages if msg.get('threadId') not in processed_threads]

        # Deduplicate within this run by threadId to avoid reprocessing same thread twice
        seen = set()
        deduped = []
        for msg in messages:
            tid = msg.get('threadId')
            if not tid or tid in seen:
                continue
            seen.add(tid)
            deduped.append(msg)
        messages = deduped

        if len(messages) < original_count:
            logger.info(f"Skipped {original_count - len(messages)} already-processed threads")

        if not messages:
            logger.info("All messages already processed!")
            if report_only:
                logger.info(f"[REPORT] Total found: {original_count} | Already processed (in DB): {original_count} | New to process: 0")
            return []

        if report_only:
            logger.info(f"[REPORT] Total found: {original_count} | Already processed (in DB): {original_count - len(messages)} | New to process: {len(messages)}")
            return []

        logger.info(f"Processing {len(messages)} NEW messages...")

        # Process each with progress bar
        results = []
        
        with tqdm(total=len(messages), desc="Extracting leads") as pbar:
            for msg in messages:
                thread_id = msg.get('threadId')
                
                try:
                    # Read thread early to optionally skip multi-message conversations
                    thread = read_gmail_thread(
                        thread_id=thread_id,
                        include_full_messages=True
                    )

                    if skip_multi_message_threads and thread.get('messages') and len(thread['messages']) > 1:
                        logger.info(f"Skipping thread {thread_id} (multi-message conversation)")
                        pbar.update(1)
                        continue

                    # Extract
                    lead_data = self.extract_client_from_thread(thread_id, preloaded_thread=thread, agent_email=agent_email)
                    results.append(lead_data)
                    
                    # Skip duplicates in auto-save
                    if lead_data.get('is_duplicate') and auto_save:
                        logger.info(f"Skipping duplicate: {lead_data['client_name']}")
                        pbar.update(1)
                        continue
                    
                    # Auto-save or manual review
                    if auto_save and lead_data.get('confidence') == 'high':
                        self.save_to_supabase(lead_data)
                    elif not auto_save:
                        # Manual review
                        self._review_lead(lead_data)

                    # Note: Rate limiting is now handled by _wait_for_rate_limit() before each API call

                except Exception as e:
                    error_str = str(e)
                    logger.error(f"Failed to process {thread_id}: {e}")

                    # Check if it's a rate limit error - wait longer
                    if '429' in error_str or 'rate_limit' in error_str.lower():
                        logger.info("Rate limit hit - waiting 65 seconds before next request...")
                        time.sleep(65)  # Wait full minute + buffer for rate limit reset
                    elif 'prompt is too long' in error_str.lower():
                        logger.warning(f"Thread {thread_id} exceeds token limit even after truncation - skipping")
                        time.sleep(5)  # Brief pause, skip this thread
                    else:
                        # Other errors - still wait to avoid rapid fire
                        logger.info("Waiting 30 seconds after error...")
                        time.sleep(30)

                pbar.update(1)
        
        # Export to CSV
        if export_csv and results:
            self.export_to_csv(results)
        
        logger.info(f"Completed: {len(results)} leads extracted")
        return results
    
    def _review_lead(self, data: Dict):
        """Interactive review of extracted lead"""
        
        print(f"\n{'='*70}")
        print(f"LEAD: {data.get('client_name', 'Unknown')}")
        print(f"{'='*70}")
        
        # Duplicate warning
        if data.get('is_duplicate'):
            print(f"\n⚠️  DUPLICATE DETECTED - Already in database (ID: {data.get('duplicate_id')})")
        
        for key, value in data.items():
            if value is not None and key not in ['thread_id', 'attachments', 'extracted_at', 'is_duplicate', 'duplicate_id']:
                if key == 'policy_numbers' and isinstance(value, list):
                    print(f"  {key:20s}: {', '.join(value)}")
                else:
                    print(f"  {key:20s}: {value}")
        
        # Show attachments
        if data.get('attachments'):
            print(f"\n  Attachments ({len(data['attachments'])}):")
            for att in data['attachments']:
                print(f"    - {att['filename']}")
        
        # Show Drive link
        if data.get('drive_folder_url'):
            print(f"\n  📁 Google Drive: {data['drive_folder_url']}")
        
        # Warnings
        if data.get('confidence') != 'high':
            print(f"\n⚠️  CONFIDENCE: {data.get('confidence', 'unknown').upper()}")
        
        required = ['client_name', 'client_phone', 'referring_agent']
        missing = [f for f in required if not data.get(f)]
        if missing:
            print(f"\n⚠️  MISSING: {', '.join(missing)}")
        
        # Action
        if data.get('is_duplicate'):
            action = input("\n[U]pdate existing, [Skip]: ").upper()
            if action == 'U':
                # Update logic here
                print("Update not implemented yet")
        else:
            action = input("\n[S]ave, [E]dit, [Skip]: ").upper()
            
            if action == 'S':
                self.save_to_supabase(data)
            elif action == 'E':
                data = self._manual_edit(data)
                self.save_to_supabase(data)
            else:
                print("⏭️  Skipped")
    
    def _manual_edit(self, data: Dict) -> Dict:
        """Manual editing interface"""
        print("\n📝 EDIT MODE (press Enter to keep current value)")
        
        editable_fields = [
            'client_name', 'client_phone', 'client_email', 
            'monthly_premium', 'annual_income', 'zip_code'
        ]
        
        for field in editable_fields:
            current = data.get(field)
            new_value = input(f"{field} [{current}]: ").strip()
            if new_value:
                data[field] = new_value
        
        return data


# Updated Supabase Schema
SUPABASE_SCHEMA = """
-- Leads table
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_name TEXT NOT NULL,
  client_phone TEXT NOT NULL,
  client_email TEXT,
  monthly_premium NUMERIC,
  aca_premium NUMERIC,
  annual_income INTEGER,
  referring_agent TEXT NOT NULL,
  application_number TEXT,
  policy_numbers TEXT[],
  household_size INTEGER,
  zip_code TEXT,
  date_of_birth DATE,
  dependents TEXT,
  contact_notes TEXT,
  thread_id TEXT UNIQUE NOT NULL,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  drive_folder_url TEXT,
  is_duplicate BOOLEAN DEFAULT FALSE,
  status TEXT DEFAULT 'pending_review',
  extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attachments table
CREATE TABLE attachments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  mime_type TEXT,
  local_path TEXT,
  attachment_id TEXT,
  message_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_leads_referring_agent ON leads(referring_agent);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_extracted_at ON leads(extracted_at);
CREATE INDEX idx_leads_client_phone ON leads(client_phone);
CREATE INDEX idx_leads_is_duplicate ON leads(is_duplicate);
CREATE INDEX idx_attachments_lead_id ON attachments(lead_id);
"""


# CLI Interface
def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract ACA leads from Gmail')
    parser.add_argument('--agent', help='Filter by agent email')
    parser.add_argument('--after', help='Filter by date (YYYY/MM/DD)')
    parser.add_argument('--before', help='Filter before date (YYYY/MM/DD)')
    parser.add_argument('--max', type=int, default=100, help='Max results')
    parser.add_argument('--auto-save', action='store_true', help='Auto-save high confidence leads')
    parser.add_argument('--no-csv', action='store_true', help='Skip CSV export')
    parser.add_argument('--report-only', action='store_true', help='Only show counts (total/processed/new) without extracting or saving')
    parser.add_argument('--export-all-leads', action='store_true', help='Export Supabase leads to a CSV and exit')
    parser.add_argument('--export-path', default='exports/leads_rows.csv', help='Destination CSV path for --export-all-leads')
    parser.add_argument('--export-agent-email', help='Agent email to filter exported leads (e.g., danielberman.ushealth@gmail.com)')
    parser.add_argument('--labels', help='Comma-separated Gmail labels to include (overrides defaults)')
    parser.add_argument('--skip-multi-message-threads', action='store_true', help='Skip threads with more than one message')
    parser.add_argument('--allow-drive', action='store_true', help='Include has:drive in addition to has:attachment')
    parser.add_argument('--ignore-default-excludes', action='store_true', help='Do not add default excluded labels (e.g., all-wraps-to-be-worked)')
    
    args = parser.parse_args()
    
    if args.export_all_leads:
        export_all_leads(args.export_path, args.export_agent_email)
        return
    
    labels_override = None
    if args.labels:
        labels_override = [label.strip() for label in args.labels.split(',') if label.strip()]

    extractor = LeadExtractor()
    extractor.process_batch(
        agent_email=args.agent,
        after_date=args.after,
        before_date=args.before,
        max_results=args.max,
        auto_save=args.auto_save,
        export_csv=not args.no_csv,
        report_only=args.report_only,
        included_labels=labels_override,
        skip_multi_message_threads=args.skip_multi_message_threads,
        allow_drive=args.allow_drive,
        ignore_default_excludes=args.ignore_default_excludes
    )


def export_all_leads(csv_path: str, agent_email: Optional[str] = None):
    """
    Export all leads from Supabase to a single CSV file.
    """
    from supabase import create_client

    supabase_url = CONFIG['supabase_url']
    supabase_key = CONFIG['supabase_key']

    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials missing; set SUPABASE_URL and SUPABASE_KEY.")
        return

    supabase = create_client(supabase_url, supabase_key)

    try:
        query = supabase.table('leads').select('*')

        # If agent_email specified, filter on referring_agent using the mapped display name
        if agent_email:
            agent_name = AGENT_EMAILS.get(agent_email, agent_email)
            query = query.eq('referring_agent', agent_name)

        result = query.execute()
        rows = result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch leads from Supabase: {e}")
        return

    if not rows:
        logger.info("No leads found in Supabase; nothing to export.")
        return

    # Ensure export directory exists
    export_path = Path(csv_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    # Fixed column order to match existing leads_rows.csv
    fieldnames = [
        'id', 'client_name', 'client_phone', 'client_email',
        'monthly_premium', 'aca_premium', 'annual_income',
        'referring_agent', 'application_number', 'policy_numbers',
        'household_size', 'zip_code', 'date_of_birth', 'dependents',
        'contact_notes', 'thread_id', 'confidence', 'drive_folder_url',
        'is_duplicate', 'status', 'extracted_at', 'created_at', 'updated_at'
    ]

    with open(export_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            # Normalize list/dict fields to strings
            for key, value in list(row.items()):
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
            writer.writerow(row)

    if agent_email:
        agent_name = AGENT_EMAILS.get(agent_email, agent_email)
        logger.info(f"Exported {len(rows)} leads for agent '{agent_name}' to {export_path}")
    else:
        logger.info(f"Exported {len(rows)} leads to {export_path}")


if __name__ == '__main__':
    main()
