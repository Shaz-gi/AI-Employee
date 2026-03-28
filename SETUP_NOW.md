# 🚀 Quick Setup - 5 Minutes to Working AI

## ⚠️ Current Issue

Your `.env` file has a **placeholder** API key. You need your **actual** key.

---

## Step 1: Get FREE Gemini API Key (3 min)

### Visit Google AI Studio
```
👉 https://aistudio.google.com/app/apikey
```

### Create Key
1. **Sign in** with Google account
2. Click **"Create API Key"**
3. Choose or create a project
4. **Copy the key** (starts with `AIzaSy...`)

**✅ No credit card required!**

---

## Step 2: Add to .env File (1 min)

### Open .env
```cmd
notepad .env
```

### Replace the placeholder:

**❌ OLD (placeholder):**
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**✅ NEW (your actual key):**
```env
GEMINI_API_KEY=AIzaSyD-your_actual_key_from_google
```

### Save the file

---

## Step 3: Test It Works (1 min)

```cmd
python check_gemini_models.py
```

**Expected Output:**
```
🧠 Google Gemini - Available Models
============================================================
✅ API Key validated!

⚡ Flash Models:
  • models/gemini-1.5-flash-002
  • models/gemini-1.5-flash-001

🧠 Pro Models:
  • models/gemini-1.5-pro-002

💡 Using model: gemini-1.5-flash-002
```

---

## Step 4: Run AI Employee

```cmd
python test_gemini.py "Hello! Are you working?"
```

**Expected:**
```
🧠 Google Gemini Brain (FREE API)
============================================================
✓ API Key found
✓ Model: gemini-1.5-flash-002
✓ FREE Tier: 60 req/min, 1,500 req/day
============================================================

📋 Analysis:
The user is testing if the system is operational...

✅ Success! Gemini is working!
```

---

## 🎯 Then Use Your AI Employee

```cmd
# Start the orchestrator
python src/orchestrator.py AI_Employee_Vault

# Drop a file for processing
echo Please summarize this > AI_Employee_Vault\Inbox\Drop\test.txt

# Watch AI process it automatically!
```

---

## 🆘 Still Having Issues?

### "API key not valid"
- Make sure you copied the **entire** key
- No spaces before or after
- No quotes around it

### "No models available"
- Your API key might be new - wait 2 minutes
- Or try creating a new key

### "Module not found"
```cmd
pip install google-generativeai python-dotenv
```

---

## 📚 Need More Help?

- **Full Guide**: GEMINI_SETUP.md
- **Quick Reference**: GEMINI_COMPLETE.md
- **Main Docs**: README.md

---

**Once you add your real API key, everything works automatically! 🎉**
