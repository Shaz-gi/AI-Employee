# 🚀 Multi-User Email Fetcher - Complete Setup

## ✨ What We Built

A **production-ready multi-user system** where:

- ✅ Each user signs up with Google
- ✅ Each user connects their Gmail
- ✅ Each user gets their own vault
- ✅ Emails are completely isolated per user
- ✅ UI shows only that user's emails
- ✅ Background fetcher handles ALL users automatically

---

## 📊 Architecture

```
User 1 signs up with Google
  ↓
Gmail OAuth connected
  ↓
Personal Vault created (Vault 1)
  ↓
Email Fetcher fetches User 1's Gmail
  ↓
Emails stored in Vault 1
  ↓
User 1 sees ONLY their emails

---

User 2 signs up with Google
  ↓
Gmail OAuth connected
  ↓
Personal Vault created (Vault 2)
  ↓
Email Fetcher fetches User 2's Gmail
  ↓
Emails stored in Vault 2
  ↓
User 2 sees ONLY their emails

---

Multi-User Email Fetcher runs continuously:
  • Checks all users every 60 seconds
  • Fetches emails for each user
  • Stores in user's personal vault
  • Updates last sync time
```

---

## 📋 Setup Steps

### Step 1: Run Database Setup

**Go to:** https://supabase.com/dashboard

**Open SQL Editor and run:**

```bash
# File location:
multi_user_gmail_setup.sql
```

**Copy all content → Paste in SQL Editor → Click Run**

This creates:
- ✅ Gmail token storage per user
- ✅ Improved triggers for Google signups
- ✅ Functions for multi-user support
- ✅ Proper RLS policies
- ✅ User dashboard view

---

### Step 2: Update Batch File

**Open:** `start_multi_user_fetcher.bat`

**Replace with your credentials:**

```batch
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key
set SUPABASE_SERVICE_KEY=your-service-role-key
```

---

### Step 3: Run Multi-User Fetcher

**Double-click:**
```
start_multi_user_fetcher.bat
```

**Or run manually:**

```bash
cd C:\Users\LENOVO\Desktop\ai-employee\AI-Employee

set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key
set SUPABASE_SERVICE_KEY=your-service-role-key

C:\Users\LENOVO\AppData\Local\Programs\Python\Python314\python.exe src\multi_user_email_fetcher.py
```

---

## 🎯 What You'll See

### Terminal Output:

```
============================================================
🚀 Starting Multi-User Real-Time Email Fetcher
============================================================
This will automatically:
  1. Check for users with Gmail connected
  2. Fetch emails for EACH user
  3. Store in user's personal vault
  4. Emails appear in UI automatically
  5. Check all users every 60 seconds
============================================================

📋 Fetching active users...
   ✓ Found 2 active user(s)
   • user1@gmail.com (user1@gmail.com) - Last sync: 5m ago
   • user2@gmail.com (user2@gmail.com) - Last sync: 10m ago

📧 Fetching emails for user1@gmail.com (user1@gmail.com)...
   Fetching unread emails...
   Found 5 emails
   ✓ Created email: Welcome to LinkedIn
   ✓ Created email: Security alert
   ...
   ✅ Fetched 5 emails for user1@gmail.com

📧 Fetching emails for user2@gmail.com (user2@gmail.com)...
   Fetching unread emails...
   Found 3 emails
   ✓ Created email: Project Update
   ✓ Created email: Meeting Reminder
   ...
   ✅ Fetched 3 emails for user2@gmail.com

🎉 Total: 8 new emails fetched across all users!

⏰ Waiting 60 seconds before next check...
```

---

## 📊 Database Structure

### Per User:

```
User Account (auth.users)
  ↓
Profile (public.profiles)
  - gmail_connected: true
  - gmail_email: user@gmail.com
  - gmail_fetch_enabled: true
  ↓
Personal Vault (public.vaults)
  - user_id: [user's ID]
  - name: "My Vault"
  ↓
Emails (public.emails)
  - user_id: [user's ID]
  - vault_id: [user's vault]
  - from_address, subject, etc.
  ↓
Gmail Tokens (public.gmail_tokens)
  - user_id: [user's ID]
  - access_token, refresh_token
```

### Isolation:

```
User 1 → Vault 1 → Emails 1 → User 1 sees ONLY these
User 2 → Vault 2 → Emails 2 → User 2 sees ONLY these
User 3 → Vault 3 → Emails 3 → User 3 sees ONLY these
```

---

## 🧪 Test Multi-User Setup

### Test User 1:

1. **Open:** http://localhost:3000/signup
2. **Click:** "Continue with Google"
3. **Sign in** with user1@gmail.com
4. **Go to:** http://localhost:3000/emails
5. **Should see:** User 1's emails only

### Test User 2:

1. **Logout** from User 1
2. **Open:** http://localhost:3000/signup
3. **Click:** "Continue with Google"
4. **Sign in** with user2@gmail.com (DIFFERENT account)
5. **Go to:** http://localhost:3000/emails
6. **Should see:** User 2's emails only (NOT User 1's!)

### Check Email Fetcher:

```
📋 Fetching active users...
   ✓ Found 2 active user(s)
   • user1@gmail.com - Last sync: 2m ago
   • user2@gmail.com - Last sync: 1m ago

📧 Fetching emails for user1@gmail.com...
   ✅ Fetched 5 emails

📧 Fetching emails for user2@gmail.com...
   ✅ Fetched 3 emails

🎉 Total: 8 new emails fetched across all users!
```

---

## 🔐 Security (RLS Policies)

### Emails Table:

```sql
-- Users can ONLY see their own emails
CREATE POLICY "Users can view own emails"
ON public.emails FOR SELECT
USING (
    user_id = auth.uid() 
    OR vault_id IN (
        SELECT id FROM public.vaults WHERE user_id = auth.uid()
    )
);
```

**This ensures:**
- ✅ User 1 can't see User 2's emails
- ✅ User 2 can't see User 1's emails
- ✅ Complete isolation
- ✅ Production-ready security

---

## 📈 Monitoring

### Check User Stats:

```sql
SELECT * FROM public.user_email_stats
ORDER BY total_emails DESC;
```

**Shows:**
- Total emails per user
- New emails count
- Pending approvals
- Sent emails

### Check Active Users:

```sql
SELECT * FROM public.get_active_gmail_users();
```

**Shows:**
- All users with Gmail connected
- Last sync time
- Vault ID

---

## ✅ Success Checklist

Your multi-user system is working when:

- [ ] Database setup SQL ran successfully
- [ ] Multi-user fetcher is running
- [ ] User 1 signs up with Google
- [ ] User 1's vault is created automatically
- [ ] User 1's emails are fetched
- [ ] User 2 signs up with Google
- [ ] User 2's vault is created automatically
- [ ] User 2's emails are fetched
- [ ] User 1 sees ONLY their emails
- [ ] User 2 sees ONLY their emails
- [ ] Fetcher checks all users every 60 seconds
- [ ] Last sync time updates

---

## 🎉 You're Done!

Your **production-ready multi-user AI Employee** is now:

- ✅ Fetching emails for ALL users
- ✅ Each user has their own vault
- ✅ Complete email isolation
- ✅ Automatic background syncing
- ✅ Real-time UI updates
- ✅ Secure RLS policies

**Test with multiple users and watch the magic happen!** 🚀

---

*Built for scale - supports unlimited users!*
