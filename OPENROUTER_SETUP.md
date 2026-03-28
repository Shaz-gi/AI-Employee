# OpenRouter Setup Guide - FREE AI API

## 🎉 Why OpenRouter?

**OpenRouter** provides **FREE** access to multiple AI models without needing credit cards or multiple API keys:

- ✅ **FREE tier** - No credit card required
- ✅ **Multiple models** - Llama, Qwen, Mistral, Gemma
- ✅ **Simple API** - Works with OpenAI SDK
- ✅ **Pay-as-you-go** - Very cheap for paid models

---

## Step 1: Get FREE API Key

### Visit OpenRouter
```
1. Go to: https://openrouter.ai/
2. Click "Sign In" (top right)
3. Sign in with Google, GitHub, or Email
4. No credit card required!
```

### Create API Key
```
1. Go to: https://openrouter.ai/keys
2. Click "Create Key"
3. Give it a name (e.g., "AI Employee")
4. Copy your key (starts with `sk-or-`)
```

**Important:** Save your API key somewhere safe!

---

## Step 2: Configure AI Employee

### Edit .env File

```cmd
# Windows
notepad .env

# Linux/Mac
nano .env
```

### Add Your API Key

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free
```

---

## Step 3: Install Dependencies

```bash
# Navigate to project
cd C:\Users\LENOVO\Desktop\ai-employee\AI-Employee

# Install OpenAI SDK (works with OpenRouter)
pip install openai python-dotenv

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 4: Test OpenRouter

### Quick Test
```cmd
# Test with simple prompt
python test_openrouter.py "What is 2 + 2?"

# Expected output:
# 🧠 OpenRouter Brain (FREE API)
# ✓ API Key found
# ✓ Model: meta-llama/llama-3-8b-instruct:free
# 📋 Analysis: This is a simple arithmetic question...
# ✅ Success!
```

### List Available Models
```cmd
# See all free and paid models
python test_openrouter.py --list-models
```

### Test with File
```cmd
# Process a file from Needs_Action folder
python test_openrouter.py --file AI_Employee_Vault\Needs_Action\FILE_test_document.md
```

### Interactive Mode
```cmd
# Chat with the AI
python test_openrouter.py

# Then type your messages:
> Summarize this text: Artificial intelligence is transforming...
> Draft an email to my boss about taking vacation
> quit
```

---

## 🆓 Free Models Available

| Model | Provider | Best For |
|-------|----------|----------|
| `meta-llama/llama-3-8b-instruct:free` | Meta | General tasks (Recommended) |
| `google/gemma-2-9b-it:free` | Google | Creative writing |
| `mistralai/mistral-7b-instruct:free` | Mistral AI | Fast responses |
| `qwen/qwen-2-7b-instruct:free` | Alibaba | Multi-language |

### Change Model

Edit `.env`:
```env
# Use Llama 3
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free

# Use Gemma
OPENROUTER_MODEL=google/gemma-2-9b-it:free

# Use Mistral
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

Or command line:
```cmd
python test_openrouter.py "Hello" --model google/gemma-2-9b-it:free
```

---

## Step 5: Run AI Employee

### Start Orchestrator
```cmd
# Start the orchestrator (uses OpenRouter automatically)
python src/orchestrator.py AI_Employee_Vault

# Run once for testing
python src/orchestrator.py AI_Employee_Vault --once
```

### Drop a File
```cmd
# Create a test file
echo Please summarize this document > AI_Employee_Vault\Inbox\Drop\test.txt

# Wait ~5 seconds for processing
# Check Plans folder for AI-generated plan
dir AI_Employee_Vault\Plans
```

---

## 💰 Paid Models (Optional)

OpenRouter also offers paid models at very low costs:

| Model | Cost per 1K tokens | Best For |
|-------|-------------------|----------|
| `meta-llama/llama-3-70b-instruct` | ~$0.0009 | Complex reasoning |
| `google/gemini-pro-1.5` | ~$0.0005 | Multi-modal tasks |
| `anthropic/claude-3-haiku` | ~$0.0003 | Fast & accurate |

### Add Credits (Optional)
```
1. Visit: https://openrouter.ai/credits
2. Add minimum $1 (no subscription)
3. Use for paid models
```

### Use Paid Model
```env
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct
```

---

## 🔧 Troubleshooting

### Error: "API_KEY not set"

```cmd
# Check if .env file exists
dir .env

# Check if API key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Key:', os.getenv('OPENROUTER_API_KEY'))"

# If None, edit .env and add:
# OPENROUTER_API_KEY=sk-or-v1-your_key
```

### Error: "Authentication failed"

1. Verify API key format (should start with `sk-or-`)
2. Check for extra spaces in `.env`
3. Test key on OpenRouter website
4. Make sure account is verified

### Error: "insufficient_quota"

This means free tier is exhausted for the day.

**Solutions:**
1. Wait for daily reset (midnight UTC)
2. Try a different free model
3. Add $1 credit (optional)

### Error: "openai not installed"

```cmd
pip install openai
```

---

## 📊 Monitor Usage

### Check Usage Dashboard
```
1. Visit: https://openrouter.ai/activity
2. See your API usage
3. Monitor token consumption
```

### Set Limits
```
OpenRouter has built-in rate limits:
- Free tier: ~20 requests/minute
- Paid tier: Higher limits

No need to worry for normal AI Employee usage!
```

---

## 🎯 Best Practices

### 1. Use Free Models First
```env
# Start with free models
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free
```

### 2. Upgrade Only If Needed
```
Free models work great for:
- Email drafting
- Document summarization
- Task planning
- Basic classification

Consider paid models for:
- Complex reasoning
- Very long documents
- Specialized tasks
```

### 3. Monitor Token Usage
```
- Typical action file: 500-1000 tokens
- Free tier: ~100,000 tokens/day
- That's 100-200 actions per day FREE!
```

---

## 📚 API Reference

### Python Usage
```python
from openrouter_brain import OpenRouterBrain

# Initialize
brain = OpenRouterBrain(
    api_key="sk-or-v1-your_key",
    model="meta-llama/llama-3-8b-instruct:free"
)

# Process text
result = brain.process_text("Summarize this document...")

# Process file
result = brain.process_action_file("path/to/file.md")

# Create plan
plan_path = brain.create_plan_file(
    "path/to/action_file.md",
    "output/directory/"
)
```

### Available Methods
```python
# Process action file
brain.process_action_file("path/to/file.md")

# Process text
brain.process_text("Your text", task="Summarize")

# Summarize document
brain.summarize_document(long_text)

# Draft email
brain.draft_email_reply(email, tone="professional")

# List models
models = brain.list_models()
```

---

## 🔗 Resources

- **OpenRouter Website**: https://openrouter.ai/
- **API Keys**: https://openrouter.ai/keys
- **Usage Dashboard**: https://openrouter.ai/activity
- **Credits**: https://openrouter.ai/credits
- **Model List**: https://openrouter.ai/models
- **API Docs**: https://openrouter.ai/docs

---

## 🎉 You're All Set!

OpenRouter provides the easiest way to get started with AI:

1. ✅ Get FREE API key (no credit card)
2. ✅ Configure `.env` file
3. ✅ Test with `python test_openrouter.py`
4. ✅ Run AI Employee!

**Happy automating! 🚀**

---

*Built with OpenRouter - Personal AI Employee Hackathon 0*
