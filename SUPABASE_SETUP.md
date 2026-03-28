# 🚀 Supabase Setup Guide - FREE Multi-Tenant Backend

## What You'll Get (100% FREE)

✅ **Authentication** - Email/password, OAuth (Google, GitHub)  
✅ **PostgreSQL Database** - 500MB (holds ~500K users)  
✅ **File Storage** - 1GB for vault files  
✅ **Row-Level Security** - Multi-tenant isolation  
✅ **50,000 MAU** - Monthly active users  
✅ **No Credit Card** required  

---

## Step 1: Create Supabase Account (2 minutes)

1. **Go to** https://supabase.com
2. Click **"Start your project"** or **"Sign In"**
3. Sign up with:
   - GitHub (recommended)
   - Google
   - Email

---

## Step 2: Create New Project (3 minutes)

1. Click **"New Project"** in dashboard
2. Fill in:
   ```
   Name: ai-employee-pro
   Database Password: [Save this securely!]
   Region: Choose closest to you (e.g., us-east-1)
   ```
3. Click **"Create new project"**
4. Wait 2-3 minutes for setup

---

## Step 3: Get Your Credentials (1 minute)

1. Go to **Settings** (gear icon) → **API**
2. Copy these values:
   ```
   Project URL: https://xxxxxxxxxxxxx.supabase.co
   API Keys:
     - anon/public: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     - service_role: [Keep this SECRET!]
   ```

---

## Step 4: Set Up Database (5 minutes)

### Option A: Run SQL in Supabase Dashboard

1. Go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy entire content from `supabase_schema.sql`
4. Paste into editor
5. Click **"Run"** (or press Ctrl+Enter)
6. Wait for "Success. No rows returned"

**Done!** Your database is ready.

### Option B: Use CLI (Advanced)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Push schema
supabase db push
```

---

## Step 5: Configure Environment (1 minute)

Create `.env` file in project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... [Keep secret!]

# Your AI Employee settings
OPENROUTER_API_KEY=sk-or-v1-your-key
```

**Important:**
- ✅ Add `.env` to `.gitignore`
- ✅ Never commit credentials to git
- ✅ Use `SUPABASE_ANON_KEY` in frontend
- ✅ Use `SUPABASE_SERVICE_KEY` only in backend

---

## Step 6: Install Python Dependencies (1 minute)

```bash
pip install supabase python-dotenv
```

---

## Step 7: Test Connection (2 minutes)

```bash
# Set environment variables (Windows)
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-anon-key

# Or (Linux/Mac)
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your-anon-key

# Test
cd src
python supabase_client.py
```

**Expected Output:**
```
✓ Connected to Supabase: https://xxx.supabase.co
✓ User created: test@example.com
✓ Signed in: test@example.com
✓ Vault created: My First Vault
✓ Test complete!
```

---

## 🎯 What's Been Created

### Database Tables

| Table | Purpose |
|-------|---------|
| `profiles` | User data, subscription plan, usage limits |
| `vaults` | User vaults (isolated per user) |
| `emails` | Processed emails with AI analysis |
| `linkedin_posts` | Scheduled/published posts |
| `audit_logs` | Compliance & audit trail |
| `usage_tracking` | Monthly usage for billing |
| `api_keys` | Developer API access |

### Security Features

✅ **Row-Level Security (RLS)** - Users can ONLY see their own data  
✅ **Encrypted passwords** - bcrypt hashing  
✅ **JWT tokens** - Secure session management  
✅ **Private storage** - Files isolated per user  

---

## 📊 Free Tier Limits

| Resource | Free Tier | What It Means |
|----------|-----------|---------------|
| **Monthly Active Users** | 50,000 | ~1,666 daily users |
| **Database Size** | 500 MB | ~500K users with basic data |
| **File Storage** | 1 GB | ~10K vault files |
| **Egress (Bandwidth)** | 5 GB/month | Plenty for API calls |
| **API Requests** | Unlimited | No rate limiting |

**When you outgrow free tier:**
- Pro Plan: $25/month (100K MAU, 8GB DB, 100GB storage)
- Still cheap for thousands of users!

---

## 🔐 Security Best Practices

### 1. Never Expose Service Role Key

```python
# ✅ GOOD: Use anon key in frontend
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ❌ BAD: Never use service key in frontend
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
```

### 2. Row-Level Security is Automatic

All tables have RLS policies. Users can ONLY access their own data:

```sql
-- Example policy (already created)
Users can view own vaults:
  USING (auth.uid() = user_id)
```

### 3. Validate on Backend

Even with RLS, validate in your Python code:

```python
# Check ownership before processing
vault = supabase.get_vault(vault_id)
if not vault or vault['user_id'] != current_user.id:
    raise PermissionError("Access denied")
```

---

## 🚀 Next Steps

### 1. Integrate with Orchestrator

Update `orchestrator.py` to use Supabase:

```python
from supabase_client import SupabaseClient

# Initialize
db = SupabaseClient()

# Sign in (or use session from web UI)
db.sign_in(email="user@example.com", password="password")

# Get user's vaults
vaults = db.get_vaults()

# Track email
db.track_email(
    vault_id=vaults[0]['id'],
    from_address="client@example.com",
    subject="Inquiry"
)

# Check usage limits
if not db.can_send_email():
    print("Email limit exceeded!")
```

### 2. Add Authentication to Web UI

Create login/signup pages in Flask:

```python
from flask import Flask, render_template, request, redirect, session
from supabase_client import SupabaseClient

app = Flask(__name__)
db = SupabaseClient()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        result = db.sign_in(email, password)
        
        if result['success']:
            session['user_id'] = result['user']['id']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error=result['error'])
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        result = db.sign_up(email, password, name)
        
        if result['success']:
            return redirect('/login')
        else:
            return render_template('signup.html', error=result['error'])
    
    return render_template('signup.html')
```

### 3. Multi-Tenant Orchestrator

Run separate orchestrator per user:

```python
# Get all users with active vaults
users = db.get_active_users()

for user in users:
    # Initialize client for this user
    user_db = SupabaseClient()
    user_db.user_id = user['id']
    
    # Get their vaults
    vaults = user_db.get_vaults()
    
    # Process each vault
    for vault in vaults:
        process_vault(user_db, vault)
```

---

## 🆘 Troubleshooting

### "Invalid API key"

- Check you're using `SUPABASE_ANON_KEY` (not service_role)
- Verify key is copied completely (no spaces)
- Check project is active in Supabase dashboard

### "Relation does not exist"

- Run the SQL schema in Supabase SQL Editor
- Check you're in the correct project
- Verify schema is `public`

### "Permission denied"

- RLS is working correctly!
- Make sure user is authenticated
- Check user owns the resource (vault, email, etc.)

### "Rate limit exceeded"

- Free tier has generous limits
- Check for infinite loops in your code
- Add caching where possible

---

## 📚 Resources

- **Supabase Docs**: https://supabase.com/docs
- **Python Client**: https://supabase.com/docs/reference/python
- **Row-Level Security**: https://supabase.com/docs/guides/auth/row-level-security
- **Storage**: https://supabase.com/docs/guides/storage

---

## 💰 Cost Projection

| Stage | Users/Month | Cost |
|-------|-------------|------|
| **Beta** | 0-1,000 | $0 (Free) |
| **Launch** | 1,000-10,000 | $0 (Free) |
| **Growth** | 10,000-50,000 | $0 (Free) |
| **Scale** | 50,000-100,000 | $25/mo (Pro) |
| **Enterprise** | 100,000+ | $25+/mo (Pro/Team) |

**You can serve 50,000 users for FREE!** 🎉

---

## ✅ You're Ready!

Your multi-tenant backend is ready:

1. ✅ Supabase project created
2. ✅ Database schema deployed
3. ✅ Python client configured
4. ✅ Authentication ready
5. ✅ Multi-tenant isolation enabled
6. ✅ Usage tracking ready
7. ✅ Audit logging enabled

**Next:** Integrate with your AI Employee! 🚀

---

*Built with ❤️ using Supabase Free Tier*
