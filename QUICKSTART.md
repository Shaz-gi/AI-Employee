# 🚀 OpenRouter Quick Start - 5 Minutes to FREE AI

## Step 1: Get FREE API Key (2 minutes)

```
1. Visit: https://openrouter.ai/keys
2. Click "Sign In" (use Google/GitHub/Email)
3. Click "Create Key"
4. Name it: "AI Employee"
5. Copy the key (starts with sk-or-v1-)
```

**✅ No credit card required!**

---

## Step 2: Configure (1 minute)

```cmd
# Edit .env file
notepad .env

# Add your API key:
OPENROUTER_API_KEY=sk-or-v1-your_key_here
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free
```

---

## Step 3: Install (1 minute)

```cmd
cd C:\Users\LENOVO\Desktop\ai-employee\AI-Employee
pip install openai python-dotenv
```

---

## Step 4: Test (1 minute)

```cmd
# Test OpenRouter
python test_openrouter.py "What is the capital of France?"

# Expected output:
# 🧠 OpenRouter Brain (FREE API)
# ✓ API Key found
# ✓ Model: meta-llama/llama-3-8b-instruct:free
# 📋 Analysis: Paris is the capital...
# ✅ Success!
```

---

## Step 5: Run AI Employee

```cmd
# Start the system
python src/orchestrator.py AI_Employee_Vault

# Drop a file for processing
echo Please summarize this > AI_Employee_Vault\Inbox\Drop\test.txt

# Watch AI process it automatically!
```

---

## 🎉 You're Done!

**FREE Models Available:**
- `meta-llama/llama-3-8b-instruct:free` ⭐ Recommended
- `google/gemma-2-9b-it:free`
- `mistralai/mistral-7b-instruct:free`
- `qwen/qwen-2-7b-instruct:free`

**Change model in `.env`:**
```env
OPENROUTER_MODEL=google/gemma-2-9b-it:free
```

---

## 📚 Need Help?

- **Full Guide**: OPENROUTER_SETUP.md
- **Commands**: COMMANDS.md
- **Test Script**: python test_openrouter.py --help

---

*Built with ❤️ using OpenRouter - FREE AI for Everyone!*
