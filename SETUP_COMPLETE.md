# ✅ AI Employee - OpenRouter Setup Complete!

## 🎉 Your AI Employee Uses OpenRouter + FREE Models

Your system is configured to use **OpenRouter's FREE tier** with automatic fallback when models are rate-limited.

---

## ⚠️ IMPORTANT: You Still Need an API Key

Your `.env` file has: `OPENROUTER_API_KEY=your_openrouter_api_key_here`

**You need to replace this with your actual API key!**

### Get FREE API Key (2 min)
```
1. Visit: https://openrouter.ai/keys
2. Sign in (Google/GitHub/Email)
3. Click "Create Key"
4. Copy the key (starts with sk-or-v1-)
```

### Add to .env
```cmd
notepad .env

# Replace with your actual key:
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
```

---

## 🤖 Available FREE Models

The system will **automatically try these in order** until one works:

| Model | Provider | Status |
|-------|----------|--------|
| `google/gemma-3n-e4b-it:free` | Google | ✅ Less crowded |
| `google/gemma-3n-e2b-it:free` | Google | ✅ Faster |
| `nvidia/nemotron-3-nano-30b-a3b:free` | NVIDIA | ✅ Available |
| `openai/gpt-oss-20b:free` | OpenAI | ✅ Available |
| `qwen/qwen3-4b:free` | Alibaba | ⚠️ Often rate-limited |

**The code automatically finds a working model!**

---

## 🧪 Test Your Setup

### Once You Have API Key
```cmd
python test_openrouter.py "Hello! Are you working?"
```

### Check Available Models
```cmd
python check_openrouter_models.py
```

---

## ▶️ Run AI Employee

```cmd
# Start orchestrator
python src/orchestrator.py AI_Employee_Vault

# Drop a file for processing
echo Please summarize this > AI_Employee_Vault\Inbox\Drop\test.txt

# Watch it get processed automatically!
```

---

## 🔧 What's Been Fixed

1. ✅ **Automatic model fallback** - Tries multiple models
2. ✅ **Rate limit handling** - Switches when model is busy
3. ✅ **Updated model list** - Uses currently available free models
4. ✅ **Better error messages** - Clear guidance when issues occur

---

## 🆘 Common Issues

### "API key not valid"
- You're using the placeholder key
- Get real key from: https://openrouter.ai/keys

### "No models available"
- All free models temporarily rate-limited
- Wait 5 minutes and try again
- Or add $1 credit for priority access

### "Module not found"
```cmd
pip install openai python-dotenv
```

---

## 📚 Documentation

- **README.md** - Main project docs
- **QUICKSTART.md** - 5-minute guide
- **COMMANDS.md** - All commands reference
- **check_openrouter_models.py** - See available models

---

## 🎯 Next Steps

1. ✅ **Get API Key** - https://openrouter.ai/keys
2. ✅ **Add to .env** - OPENROUTER_API_KEY=sk-or-v1-...
3. ✅ **Test** - python test_openrouter.py "Hello"
4. ✅ **Run** - python src/orchestrator.py AI_Employee_Vault

---

**Once you add your API key, the AI Employee will work automatically! 🚀**

The system will automatically find a working free model and process your files!

---

*Built with OpenRouter - Personal AI Employee Hackathon 0*
