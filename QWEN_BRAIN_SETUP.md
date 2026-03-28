# Qwen Brain Setup Guide

## Overview

The AI Employee now uses **Qwen** (via Alibaba DashScope API) as its reasoning engine instead of Claude Code. This makes the system fully API-driven and independent.

---

## Step 1: Get Your DashScope API Key

1. **Visit DashScope Console**
   - Go to: https://dashscope.console.aliyun.com/
   - Sign up or log in with your Alibaba Cloud account

2. **Create API Key**
   - Navigate to "API Key Management" or "Keys" section
   - Click "Create New Key"
   - Copy your API key (starts with `sk-`)

3. **Free Tier Information**
   - New users get free credits
   - Qwen-plus: Very affordable for development
   - Check pricing at: https://help.aliyun.com/zh/dashscope/pricing

---

## Step 2: Configure Environment

### Windows

```cmd
# Set environment variable (current session)
set DASHSCOPE_API_KEY=sk-your_api_key_here

# Or edit .env file
notepad .env
# Add: DASHSCOPE_API_KEY=sk-your_api_key_here
```

### Linux/Mac

```bash
# Set environment variable (current session)
export DASHSCOPE_API_KEY=sk-your_api_key_here

# Or add to ~/.bashrc for permanent
echo 'export DASHSCOPE_API_KEY=sk-your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

### Edit .env File (Recommended)

```bash
# Copy template
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac

# Edit .env file
# Add your API key:
DASHSCOPE_API_KEY=sk-your_api_key_here
QWEN_MODEL=qwen-plus
```

---

## Step 3: Install Dependencies

```bash
# Navigate to project directory
cd C:\Users\LENOVO\Desktop\ai-employee\AI-Employee

# Install Python dependencies
pip install -r requirements.txt
```

---

## Step 4: Test Qwen Brain

### Quick Test

```bash
# Test with simple prompt
python test_qwen.py "What is 2 + 2?"

# Test with file
python test_qwen.py --file AI_Employee_Vault/Needs_Action/FILE_test_document.md

# Test with verbose output
python test_qwen.py -v "Summarize: The AI Employee system uses Qwen for reasoning"
```

### Expected Output

```
✓ API Key found
✓ Model: qwen-plus
--------------------------------------------------

💬 Processing prompt...

📋 Analysis:
This is a simple arithmetic question...

📝 Suggested Actions:
  - [ ] Provide answer: 4

⚠️  Approval Required: No
📁 Category: Other

✓ Success!
```

---

## Step 5: Run the Full System

### Start Orchestrator

```bash
# Start the orchestrator (uses Qwen Brain automatically)
python src/orchestrator.py AI_Employee_Vault

# Or run once for testing
python src/orchestrator.py AI_Employee_Vault --once
```

### Drop a File for Processing

1. Create a text file with content:
   ```
   AI_Employee_Vault/Inbox/Drop/test_request.txt
   ```
   
   Content:
   ```
   Please summarize this meeting notes document and extract action items.
   
   Meeting Notes:
   - Discussed Q1 budget
   - Need to hire new developer
   - Launch date set for March 15
   ```

2. Wait ~5 seconds for watcher to detect

3. Check `AI_Employee_Vault/Needs_Action/` for action file

4. Orchestrator will process with Qwen Brain and create plan in `Plans/`

---

## Qwen Models Comparison

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| **qwen-turbo** | Simple tasks, fast responses | Fastest | Lowest |
| **qwen-plus** | Balanced performance (Recommended) | Fast | Low |
| **qwen-max** | Complex reasoning, detailed analysis | Slower | Higher |

### Change Model

Edit `.env`:
```
QWEN_MODEL=qwen-max
```

Or pass to test script:
```bash
python test_qwen.py "prompt" --model qwen-max
```

---

## Using Qwen Brain Directly

### Python Code

```python
from src.qwen_brain import QwenBrain

# Initialize
brain = QwenBrain(api_key="sk-your_key", model="qwen-plus")

# Process text
result = brain.process_text(
    "Please review this email and draft a reply",
    task="Draft a professional email response"
)

print(result['analysis'])
print(result['draft_response'])
print(result['approval_required'])

# Process action file
result = brain.process_action_file(
    "AI_Employee_Vault/Needs_Action/FILE_example.md"
)

# Create plan file
plan_path = brain.create_plan_file(
    "AI_Employee_Vault/Needs_Action/FILE_example.md",
    "AI_Employee_Vault/Plans/"
)
```

### Available Methods

```python
# Process an action file
brain.process_action_file("path/to/file.md")

# Process arbitrary text
brain.process_text("Your text here", task="Summarize this")

# Summarize document
brain.summarize_document(long_text)

# Draft email reply
brain.draft_email_reply(
    original_email,
    tone="professional",
    additional_context="Be friendly but concise"
)

# Create plan file
brain.create_plan_file(action_file_path, output_dir)
```

---

## Troubleshooting

### Error: "API_KEY not set"

```bash
# Check if .env file exists
dir .env  # Windows
ls .env   # Linux/Mac

# Check if API key is set
python -c "import os; print(os.getenv('DASHSCOPE_API_KEY'))"

# If None, edit .env and add:
# DASHSCOPE_API_KEY=sk-your_key
```

### Error: "Invalid API key"

1. Verify API key format (should start with `sk-`)
2. Check for extra spaces in `.env`
3. Test API key on DashScope console
4. Ensure account has available credits

### Error: "dashscope not installed"

```bash
pip install dashscope
# Or
pip install -r requirements.txt
```

### Qwen Brain Returns Empty Response

1. Check API key has credits
2. Try a simpler prompt
3. Check internet connection
4. Try different model (qwen-turbo is most reliable)

---

## Cost Management

### Monitor Usage

1. Visit: https://dashscope.console.aliyun.com/
2. Go to "Usage Statistics" or "Billing"
3. Monitor token consumption

### Reduce Costs

1. Use `qwen-turbo` for simple tasks
2. Set `max_tokens` lower for shorter responses
3. Use `qwen-plus` only for complex reasoning
4. Cache responses for repeated queries

### Example Cost (Approximate)

- **qwen-turbo**: ~$0.002 per 1K tokens
- **qwen-plus**: ~$0.008 per 1K tokens
- **qwen-max**: ~$0.04 per 1K tokens

Typical action file processing: 500-1000 tokens = **$0.001 - $0.04 per task**

---

## Best Practices

### 1. API Key Security

```bash
# NEVER commit .env to git
# Add to .gitignore:
.env
*.key
*.token
```

### 2. Error Handling

```python
try:
    result = brain.process_action_file(file_path)
except Exception as e:
    # Fallback to basic processing
    logger.warning(f"Qwen failed: {e}")
    create_basic_plan()
```

### 3. Rate Limits

- DashScope has rate limits (requests per minute)
- For high volume, add retry logic with delays
- Use `qwen-turbo` for bulk processing

### 4. Response Quality

- Be specific in prompts
- Provide context in `custom_instructions`
- Use appropriate temperature (0.7 is good balance)

---

## Next Steps

1. ✅ Test Qwen Brain with `test_qwen.py`
2. ✅ Configure `.env` with your API key
3. ✅ Run orchestrator: `python src/orchestrator.py AI_Employee_Vault`
4. ✅ Drop a file and watch Qwen process it
5. 🚀 Upgrade to Silver Tier with email/WhatsApp integration

---

## Resources

- **DashScope Console**: https://dashscope.console.aliyun.com/
- **Qwen Documentation**: https://help.aliyun.com/zh/dashscope/
- **Model Pricing**: https://help.aliyun.com/zh/dashscope/pricing
- **API Reference**: https://help.aliyun.com/zh/dashscope/developer-reference/

---

*Built with ❤️ using Qwen - Personal AI Employee Hackathon 0*
