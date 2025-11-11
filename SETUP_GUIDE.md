# 🚀 COMPLETE SETUP GUIDE - Extract All Gmail Deals

This guide will walk you through setting up and running the Gmail extraction script to get **ALL 201 sold deals** from Daniel Hera's emails.

---

## 📋 Prerequisites

- Python 3.7 or higher installed
- Gmail account access (chris@cjsinsurancesolutions.com)
- Internet connection
- 10-15 minutes for initial setup

---

## 🔧 STEP 1: Install Required Python Packages

Open your terminal/command prompt and run:

```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**For Windows PowerShell:**
```powershell
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**For Mac/Linux:**
```bash
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 🔐 STEP 2: Set Up Gmail API Access

### A. Go to Google Cloud Console
1. Visit: https://console.cloud.google.com
2. Sign in with your Gmail account (chris@cjsinsurancesolutions.com)

### B. Create a New Project
1. Click the project dropdown at the top
2. Click "New Project"
3. Name it: `Gmail Deal Extractor`
4. Click "Create"

### C. Enable Gmail API
1. In the search bar at top, type: `Gmail API`
2. Click on "Gmail API" in results
3. Click the blue "ENABLE" button
4. Wait for it to enable (takes 10-30 seconds)

### D. Create OAuth Credentials
1. Click "Credentials" in left sidebar (or go directly to: https://console.cloud.google.com/apis/credentials)
2. Click "+ CREATE CREDENTIALS" at top
3. Select "OAuth client ID"
4. If prompted to configure consent screen:
   - Click "CONFIGURE CONSENT SCREEN"
   - Select "External"
   - Click "CREATE"
   - Fill in:
     * App name: `Gmail Deal Extractor`
     * User support email: your email
     * Developer contact: your email
   - Click "SAVE AND CONTINUE" through all steps
   - On "Test users", click "+ ADD USERS" and add your email
   - Click "SAVE AND CONTINUE"
   - Click "BACK TO DASHBOARD"
5. Now create credentials:
   - Click "Credentials" in left sidebar again
   - Click "+ CREATE CREDENTIALS"
   - Select "OAuth client ID"
   - Application type: **Desktop app**
   - Name: `Gmail Extractor Desktop`
   - Click "CREATE"

### E. Download Credentials
1. A dialog will appear showing your Client ID
2. Click "DOWNLOAD JSON"
3. **IMPORTANT:** Rename the downloaded file to exactly: `credentials.json`
4. Save it in the same folder as your Python script

---

## 📂 STEP 3: Organize Your Files

Create a folder for this project. You should have:

```
gmail-extractor/
├── extract_all_daniel_hera_deals.py   ← The Python script
└── credentials.json                    ← Your downloaded credentials
```

**Make sure both files are in the same folder!**

---

## ▶️ STEP 4: Run the Script

### Option A: Using Terminal/Command Prompt

1. Open terminal/command prompt
2. Navigate to your folder:
   ```bash
   cd path/to/gmail-extractor
   ```
3. Run the script:
   ```bash
   python extract_all_daniel_hera_deals.py
   ```
   Or on Mac/Linux:
   ```bash
   python3 extract_all_daniel_hera_deals.py
   ```

### Option B: Using VS Code

1. Open VS Code
2. Open the folder containing your files
3. Open the terminal in VS Code (View → Terminal)
4. Run:
   ```bash
   python extract_all_daniel_hera_deals.py
   ```

---

## 🔑 STEP 5: First-Time Authentication

When you run the script for the first time:

1. **Browser window will open automatically**
2. Sign in with your Gmail account (chris@cjsinsurancesolutions.com)
3. You'll see a warning: "Google hasn't verified this app"
   - Click "Advanced"
   - Click "Go to Gmail Deal Extractor (unsafe)"
   - (This is safe - it's YOUR app)
4. Click "Allow" to give the app access to read your Gmail
5. You'll see "The authentication flow has completed"
6. **Close the browser window**
7. Return to your terminal - the script will continue automatically

**Note:** After first-time setup, a `token.json` file is created. You won't need to authenticate again unless you delete this file.

---

## ⏳ STEP 6: Wait for Extraction

The script will now:
- Search through all emails from danielhera.ushealth@gmail.com
- Filter by your sold deal labels
- Extract client data from each email
- This takes **5-10 minutes** for ~201 emails

You'll see progress updates like:
```
🔍 Searching: from:danielhera.ushealth@gmail.com ...
   Retrieved 100 messages so far...
   Retrieved 201 messages so far...
✅ Found 201 total messages

📧 Extracting deal details from each email...
   Processing message 10/201...
   Processing message 20/201...
```

---

## ✅ STEP 7: Get Your Results

When complete, you'll see:
```
✅ Extracted 201 unique sold deals!

💾 Saved to: daniel_hera_ALL_deals_20251111_143022.csv
💾 Saved to: daniel_hera_ALL_deals_20251111_143022.json

📊 EXTRACTION COMPLETE - STATISTICS
==================================================================
Total Deals Extracted: 201
ACA Deals: 150
SUPP Deals: 51
Average Income: $33.2k
Income Range: $12.0k - $115.0k

✅ All files saved to current directory!
```

Your files will be saved in the same folder with timestamped names.

---

## 📁 Output Files

You'll get 2 files:

### 1. CSV File (Excel-compatible)
- Open in Excel, Google Sheets, or any spreadsheet app
- Ready to import into your CRM
- Columns: First Name, Last Name, Phone, Email, Income, etc.

### 2. JSON File (For automation/programming)
- Use in n8n workflows
- Import into databases
- Feed into other scripts

---

## 🔧 Troubleshooting

### "credentials.json not found"
→ Make sure the file is in the same folder as the script and named exactly `credentials.json`

### "Module not found" error
→ Install packages: `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`

### "Access denied" or "Permission denied"
→ Make sure you added your email as a test user in the OAuth consent screen

### Script runs but finds 0 results
→ Check that Daniel Hera's emails have the correct labels in your Gmail

### "Python not found" error
→ Install Python from: https://www.python.org/downloads/

---

## 🎯 What's Next?

After extraction:
1. **Import to CRM:** Use the CSV to bulk import all 201 deals
2. **Cross-reference:** Check against commission records
3. **Follow-up campaigns:** Segment by ACA vs SUPP for targeted outreach
4. **Track renewals:** Set up automated renewal reminders

---

## 📞 Need Help?

If you run into issues:
1. Check the troubleshooting section above
2. Make sure all steps were followed exactly
3. Verify file names and locations
4. Check Python and package versions

---

## 🔒 Security Notes

- `credentials.json` contains your app credentials (NOT your password)
- `token.json` stores your authentication token
- **Never share these files publicly**
- Keep them secure in your local project folder
- The script only has **read-only** access to Gmail

---

## ⚡ Quick Reference Commands

**Install packages:**
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Run script:**
```bash
python extract_all_daniel_hera_deals.py
```

**Check Python version:**
```bash
python --version
```

---

**Ready to extract all 201 deals? Start with Step 1!** 🚀
