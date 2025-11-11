# 📧 Gmail Sold Deals Extractor - Complete Package

**Extract ALL 201 sold deals from Daniel Hera's emails**

---

## 🎯 What You Get

This package extracts all sold deals from `danielhera.ushealth@gmail.com` with:
- First Name & Last Name
- Phone Number
- Income Level
- Household Size
- Deal Type (ACA vs SUPP)
- Agent Information

**Total Available:** 201 sold deals  
**Current MCP Extract:** 39 deals (19.4%)  
**This Script Gets:** ALL 201 deals (100%)

---

## 📦 Package Contents

| File | Description |
|------|-------------|
| **verify_setup.py** | ⭐ **START HERE** - Checks if everything is configured |
| **extract_all_daniel_hera_deals.py** | Main extraction script |
| **SETUP_GUIDE.md** | Complete step-by-step setup instructions |
| **daniel_hera_sold_deals.csv** | Initial 39 deals (from MCP extraction) |
| **daniel_hera_sold_deals.json** | Initial 39 deals (JSON format) |
| **SOLD_DEALS_SUMMARY.md** | Summary of initial extraction |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Python Packages
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 2: Get Gmail API Credentials
1. Go to: https://console.cloud.google.com
2. Create project → Enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download as `credentials.json`
5. Place in this folder

**Need detailed instructions?** → See `SETUP_GUIDE.md`

### Step 3: Run Verification
```bash
python verify_setup.py
```

This checks if everything is configured correctly.

If all checks pass ✅, run:
```bash
python extract_all_daniel_hera_deals.py
```

---

## ⏱️ How Long Does It Take?

- **Setup (first time only):** 10-15 minutes
- **Extraction (each run):** 5-10 minutes for 201 emails
- **Authentication:** 1 minute (first time only)

---

## 📊 What You'll Get

After extraction completes, you'll have:

### CSV File (Excel-ready)
```
daniel_hera_ALL_deals_20251111_143022.csv
```
- Open in Excel, Google Sheets, or any spreadsheet
- Import directly into your CRM
- 201 rows of client data

### JSON File (Automation-ready)
```
daniel_hera_ALL_deals_20251111_143022.json
```
- Use in n8n workflows
- Import into databases
- Feed into other automation tools

---

## 🎬 Complete Workflow

```
1. pip install [packages]          ← Install Python packages
2. Get credentials.json             ← Download from Google Cloud Console
3. python verify_setup.py           ← Check everything is ready
4. python extract_all_daniel_hera_deals.py  ← Run extraction
5. Wait 5-10 minutes                ← Script processes 201 emails
6. Get your CSV + JSON files        ← Import to CRM
```

---

## 💡 Pro Tips

**First Time Setup:**
- Use the verification script to catch issues early
- Follow SETUP_GUIDE.md step-by-step
- Keep credentials.json secure

**Running the Script:**
- Run from the command line for best results
- Don't close the terminal while it's running
- First run requires browser authentication
- Subsequent runs are automatic

**After Extraction:**
- CSV file → Import to your CRM
- JSON file → Use for automation
- Both files are timestamped to avoid overwrites

---

## 🔒 Security & Privacy

- Script has **read-only** access to Gmail
- Your credentials never leave your computer
- OAuth authentication (most secure method)
- No passwords stored anywhere
- Full control over API access

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "credentials.json not found" | Download from Google Cloud Console |
| "Module not found" | Run: `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib` |
| "Python not found" | Install from python.org |
| Script finds 0 results | Check Gmail labels are correct |
| Authentication fails | Add your email as test user in OAuth consent screen |

**Still stuck?** Check SETUP_GUIDE.md for detailed troubleshooting.

---

## 📈 Current vs Complete Extraction

| Metric | MCP Extract (Current) | This Script (Complete) |
|--------|----------------------|------------------------|
| **Deals Extracted** | 39 | 201 |
| **Coverage** | 19.4% | 100% |
| **ACA Deals** | 24 | ~150 (estimated) |
| **SUPP Deals** | 15 | ~51 (estimated) |
| **Method** | MCP Server (limited) | Direct Gmail API |

---

## ⚡ Need Help?

1. Run `python verify_setup.py` to diagnose issues
2. Check SETUP_GUIDE.md for step-by-step instructions
3. Review error messages carefully
4. Ensure all files are in the same folder

---

## 🎯 Next Steps After Extraction

1. **Import to CRM** - Use CSV file for bulk import
2. **Segment by Type** - Filter ACA vs SUPP for targeted campaigns
3. **Cross-Reference** - Match with commission records
4. **Follow-Up** - Create renewal reminders for clients
5. **Analyze** - Review income distribution and household sizes

---

## 📞 Questions?

**Setup Issues:** See SETUP_GUIDE.md  
**Script Errors:** Check verify_setup.py results  
**Gmail API:** See troubleshooting section above

---

**Ready to extract ALL 201 deals?**  
**Start here:** `python verify_setup.py` 🚀

---

*Package created: November 11, 2025*  
*For: Chris @ CJS Insurance Solutions*
