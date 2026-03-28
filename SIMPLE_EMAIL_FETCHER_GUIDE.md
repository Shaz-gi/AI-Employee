# 🚀 Simple Email Fetcher - Quick Setup

## ✅ What's Different

This version uses **simple HTTP requests** instead of the complex supabase package.

**Benefits:**
- ✅ No Visual C++ Build Tools needed
- ✅ No complex dependencies
- ✅ Works immediately on Windows
- ✅ Same functionality, simpler setup

---

## 📋 Setup (3 Steps)

### Step 1: Edit Batch File

Open: `start_email_fetcher.bat`

**Replace these lines with your actual credentials:**

```batch
set SUPABASE_URL=https://vzxl...your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key-here
```

**Get your credentials from:**
```
https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
```

---

### Step 2: Run the Fetcher

**Double-click:**
```
start_email_fetcher.bat
```

**Or run manually:**

```bash
cd C:\Users\LENOVO\Desktop\ai-employee\AI-Employee

set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key

C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\simple_email_fetcher.py
```

---

### Step 3: Authenticate Gmail

**First time it runs:**

1. Browser will open automatically
2. Sign in with your Gmail account
3. Grant permissions
4. Token is saved for future use
5. Email fetching starts!

**You'll see:**

```
============================================================
🚀 Starting Simple Real-Time Email Fetcher
============================================================

📧 Fetching emails from Gmail...
   Fetching up to 20 emails...
   Found 5 emails
   ✓ Created email: Welcome to LinkedIn
   ✓ Created email: Security alert
   ...
   ✅ Fetched 5 emails

🎉 Success! 5 new emails fetched!
```

---

## 🎯 What Happens

```
1. Script runs every 30 seconds
2. Connects to your Gmail
3. Fetches unread emails
4. Stores in Supabase database
5. Emails appear in UI automatically
```

---

## 📊 Check It's Working

### In Terminal:

You should see output like:

```
⏰ [21:30:00] Fetching emails from Gmail...
   Found 3 emails
   ✓ Created email: ...
   ✅ Fetched 3 emails

🎉 Success! 3 new emails fetched!
```

### In UI:

Go to: http://localhost:3000/emails

You should see your Gmail emails appearing!

---

## 🆘 Troubleshooting

### "Supabase credentials required"

**Fix:** Edit `start_email_fetcher.bat` and add your actual Supabase URL and key

### "Gmail authentication required"

**This is normal!** First time it will:
1. Open browser
2. Ask you to sign in
3. Save token for future use

### "No emails fetched"

**Check:**
- Do you have unread emails in Gmail?
- Is Gmail API enabled in Google Cloud Console?
- Are credentials.json and token.json in src/ folder?

### "ModuleNotFoundError: No module named 'requests'"

**Fix:**

```bash
C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe -m pip install requests
```

---

## ✅ Success Checklist

Your email fetcher is working when:

- [ ] Script runs without errors
- [ ] Gmail authentication successful
- [ ] Shows "Found X emails"
- [ ] Shows "✓ Created email: ..."
- [ ] Emails appear in UI at /emails page
- [ ] New emails auto-fetch every 30 seconds

---

## 🎉 You're Done!

**Your automatic Gmail integration is now:**
- ✅ Fetching emails every 30 seconds
- ✅ Storing in database
- ✅ Showing in UI automatically
- ✅ Ready for AI analysis

**Next:** Go to http://localhost:3000/emails and see your emails! 🚀

---

*Simple, fast, and works on Windows without complex setup!*
