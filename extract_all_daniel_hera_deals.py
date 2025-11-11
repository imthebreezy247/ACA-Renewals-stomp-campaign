#!/usr/bin/env python3
"""
COMPLETE GMAIL SOLD DEALS EXTRACTOR
Extracts ALL sold deals from Daniel Hera's emails

Author: Chris @ CJS Insurance Solutions
Date: November 11, 2025
"""

import os
import re
import json
import csv
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope - we need read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate and return Gmail service object"""
    creds = None
    
    # Check if we have saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ ERROR: credentials.json not found!")
                print("\n📋 Setup Instructions:")
                print("   1. Go to: https://console.cloud.google.com")
                print("   2. Create a new project (or select existing)")
                print("   3. Enable Gmail API")
                print("   4. Create OAuth 2.0 credentials (Desktop app)")
                print("   5. Download as 'credentials.json'")
                print("   6. Place credentials.json in this directory")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'❌ An error occurred: {error}')
        return None

def search_emails(service, query, max_results=500):
    """Search for emails matching query and return all results"""
    all_messages = []
    page_token = None
    
    print(f"🔍 Searching: {query}")
    print("⏳ This may take a few minutes...\n")
    
    while True:
        try:
            if page_token:
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=100,
                    pageToken=page_token
                ).execute()
            else:
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=100
                ).execute()
            
            messages = results.get('messages', [])
            all_messages.extend(messages)
            
            print(f"   Retrieved {len(all_messages)} messages so far...")
            
            page_token = results.get('nextPageToken')
            if not page_token or len(all_messages) >= max_results:
                break
                
        except HttpError as error:
            print(f'❌ Error searching emails: {error}')
            break
    
    print(f"✅ Found {len(all_messages)} total messages\n")
    return all_messages

def get_message_details(service, message_id):
    """Get full details of a specific message"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        return message
    except HttpError as error:
        print(f'Error getting message {message_id}: {error}')
        return None

def extract_client_data(subject, snippet, body):
    """Extract name, phone, income, household from email content"""
    
    full_text = f"{subject} {snippet} {body}"
    
    # Extract phone
    phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', full_text)
    phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}" if phone_match else ""
    
    # Extract income
    income_match = re.search(r'(\d+\.?\d*k)', full_text, re.IGNORECASE)
    income = income_match.group(1) if income_match else ""
    
    # Extract household
    hh_match = re.search(r'HH(\d+)', full_text, re.IGNORECASE)
    household = f"HH{hh_match.group(1)}" if hh_match else ""
    
    if not household:
        hh_match2 = re.search(r'(\d+)HH', full_text, re.IGNORECASE)
        household = f"{hh_match2.group(1)}HH" if hh_match2 else ""
    
    # Extract name - multiple patterns
    name_patterns = [
        r'(?:signup|Signup)\s*-?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:-|\(|,)',
        r'needing a signup,?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+?)\s+\d+',
        r'\d+\.?\d*k\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    ]
    
    first_name = ""
    last_name = ""
    
    for pattern in name_patterns:
        name_match = re.search(pattern, full_text)
        if name_match:
            full_name = name_match.group(1).strip()
            full_name = re.sub(r'\s+(Hi|I have|needing)', '', full_name, flags=re.IGNORECASE).strip()
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
                break
    
    # Determine deal type
    deal_type = "ACA" if "ACA" in subject or "Aca" in subject else "SUPP"
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "income": income,
        "household": household,
        "type": deal_type
    }

def get_header_value(headers, name):
    """Extract specific header value from message headers"""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""

def main():
    print("=" * 70)
    print("  DANIEL HERA SOLD DEALS - COMPLETE EXTRACTION")
    print("  Gmail API Direct Access")
    print("=" * 70)
    print()
    
    # Authenticate
    print("🔐 Authenticating with Gmail API...")
    service = authenticate_gmail()
    
    if not service:
        print("\n❌ Failed to authenticate. Please check setup instructions above.")
        return
    
    print("✅ Authentication successful!\n")
    
    # Search query - matching your requirements
    query = """
        from:danielhera.ushealth@gmail.com 
        (label:sold-deal-paid---sold-deals OR label:processed-sold-deals-using-automation-to-final-label)
        -label:aca-leads-to-be-worked-dead-deal
        -label:aca-leads-to-be-worked-tanya-deals-processed-tanya-sold-deals
        -label:aca-leads-to-be-worked-tanya-deals-tanya-sold-deals
        -label:aca-leads-to-be-worked-tanya-deals
    """.replace('\n', ' ').strip()
    
    # Get all message IDs
    messages = search_emails(service, query, max_results=500)
    
    if not messages:
        print("❌ No messages found matching the criteria.")
        return
    
    # Extract details from each message
    print("📧 Extracting deal details from each email...")
    deals = []
    seen_phones = set()
    
    for i, msg in enumerate(messages, 1):
        if i % 10 == 0:
            print(f"   Processing message {i}/{len(messages)}...")
        
        message = get_message_details(service, msg['id'])
        if not message:
            continue
        
        # Get headers
        headers = message['payload'].get('headers', [])
        subject = get_header_value(headers, 'Subject')
        date = get_header_value(headers, 'Date')
        
        # Get snippet
        snippet = message.get('snippet', '')
        
        # Get body (simplified - you might need more complex parsing)
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
        
        # Extract client data
        client_data = extract_client_data(subject, snippet, body)
        
        # Skip if missing critical info or duplicate
        if not client_data['first_name'] or not client_data['phone']:
            continue
        
        if client_data['phone'] in seen_phones:
            continue
        
        seen_phones.add(client_data['phone'])
        
        # Add to deals list
        deal = {
            "first_name": client_data['first_name'],
            "last_name": client_data['last_name'],
            "agent_name": "Daniel Hera",
            "agent_email": "danielhera.ushealth@gmail.com",
            "phone": client_data['phone'],
            "client_email": "",
            "income": client_data['income'],
            "household": client_data['household'],
            "date": date,
            "type": client_data['type'],
            "premium": ""
        }
        deals.append(deal)
    
    print(f"\n✅ Extracted {len(deals)} unique sold deals!\n")
    
    # Save to CSV
    csv_filename = f"daniel_hera_ALL_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['first_name', 'last_name', 'agent_name', 'agent_email', 
                     'phone', 'client_email', 'income', 'household', 'date', 'type', 'premium']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deals)
    
    print(f"💾 Saved to: {csv_filename}")
    
    # Save to JSON
    json_filename = f"daniel_hera_ALL_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_filename, 'w') as jsonfile:
        json.dump(deals, jsonfile, indent=2)
    
    print(f"💾 Saved to: {json_filename}")
    
    # Print statistics
    print("\n" + "=" * 70)
    print("📊 EXTRACTION COMPLETE - STATISTICS")
    print("=" * 70)
    print(f"Total Deals Extracted: {len(deals)}")
    print(f"ACA Deals: {sum(1 for d in deals if d['type'] == 'ACA')}")
    print(f"SUPP Deals: {sum(1 for d in deals if d['type'] == 'SUPP')}")
    
    if deals:
        incomes = [float(d['income'].replace('k', '')) for d in deals if d['income'] and 'k' in d['income']]
        if incomes:
            print(f"Average Income: ${sum(incomes)/len(incomes):.1f}k")
            print(f"Income Range: ${min(incomes)}k - ${max(incomes)}k")
    
    print("\n✅ All files saved to current directory!")

if __name__ == "__main__":
    main()
