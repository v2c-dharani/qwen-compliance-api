# Fine-Tuned Qwen2.5-1.5B-Instruct Local REST API

A production-ready, lightweight REST API server built with **FastAPI**, **PyTorch**, **Transformers**, and **PEFT** to serve your local fine-tuned Qwen compliance AI model (`Qwen2.5-1.5B-Instruct` with LoRA adapter).

---

## 🏛️ Architecture Overview

```text
┌─────────────────┐
│   Website 1     │────┐
└─────────────────┘    │
┌─────────────────┐    │
│   Website 2     │────┼───> [Backend Proxy] ──(X-API-Key)──> Local FastAPI Server
└─────────────────┘    │                                              │
┌─────────────────┐    │                                              ▼
│   Website 3     │────┘                                     In-Memory Fine-Tuned
└─────────────────┘                                           Qwen LoRA Model
                                                                      │
                                                                      ▼
                                                               Formatted Answer
```

### Highlights
- **Single Model Load**: Loads the base model and LoRA adapter into RAM/VRAM **once** when the server starts.
- **Fast Sequential Inferences**: Serves back-to-back requests without reloading model weights.
- **Secure Authentication**: Protected by custom `X-API-Key` header with constant-time verification.
- **No Third-Party APIs**: 100% local model execution — zero external API calls.

---

## 📂 Model File Location Guide

Your fine-tuned model files (LoRA adapter) are located at:
`C:\Users\acer\Downloads\dharani\qwen-compliance-finetuned`

This directory contains:
- `adapter_config.json` (Specifies base model: `Qwen/Qwen2.5-1.5B-Instruct` & target modules)
- `adapter_model.safetensors` (LoRA trained weights ~73.9 MB)
- `tokenizer.json` & `tokenizer_config.json` (Qwen tokenizer files)
- `chat_template.jinja` (Chat formatting template)

The `MODEL_PATH` setting in `qwen-api/.env` points directly to this folder:
```env
MODEL_PATH=C:/Users/acer/Downloads/dharani/qwen-compliance-finetuned
```

---

## 🚀 Quickstart Guide (Windows Commands)

Follow these step-by-step commands in **Windows PowerShell** or **Command Prompt (cmd)**.

### Step 1: Open Terminal in the `qwen-api` Directory
```powershell
cd C:\Users\acer\Downloads\dharani\qwen-compliance-finetuned\qwen-api
```

### Step 2: Create a Python Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
**In PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*

**In Command Prompt (cmd):**
```cmd
venv\Scripts\activate.bat
```

### Step 4: Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env` or edit the included `.env` file:
```powershell
# In PowerShell:
Copy-Item .env.example .env
```

Ensure `.env` contains your secure key and model path:
```env
API_KEY=qw_sec_8f9a2b4c1d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a
MODEL_PATH=C:/Users/acer/Downloads/dharani/qwen-compliance-finetuned
BASE_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
MODEL_NAME=qwen-compliance
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=*
```

### Step 6: Start the REST API Server
Run the Uvicorn server command:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
> The server will start, automatically load the base model (`Qwen/Qwen2.5-1.5B-Instruct`), attach your LoRA adapter, and listen on `http://localhost:8000`.

---

## 🧪 Testing the API

### 1. Browser Health Check
Open your web browser and navigate to:
```text
http://localhost:8000/health
```
**Response:**
```json
{
  "status": "ok",
  "model": "qwen-compliance"
}
```

---

### 2. Testing with `curl` (Command Prompt / Terminal)

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: qw_sec_8f9a2b4c1d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a" \
     -d "{\"message\": \"What is NIST SP 800-53?\"}"
```

**Response:**
```json
{
  "success": true,
  "answer": "NIST SP 800-53 (Security and Privacy Controls for Information Systems and Organizations) is a benchmark database of security and privacy controls created by the National Institute of Standards and Technology..."
}
```

---

### 3. Testing with Python (`requests`)

You can run the included `test_client.py` script:
```powershell
python test_client.py
```

Or write custom Python code:
```python
import requests

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "qw_sec_8f9a2b4c1d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a"
}
payload = {
    "message": "What is CIS?"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

if data.get("success"):
    print("Answer:", data["answer"])
else:
    print("Error:", data.get("detail"))
```

---

### 4. Testing with JavaScript (`fetch` / Node.js)

```javascript
async function askQwen(question) {
  const response = await fetch("http://localhost:8000/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "qw_sec_8f9a2b4c1d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a"
    },
    body: JSON.stringify({
      message: question
    })
  });

  const data = await response.json();
  if (data.success) {
    console.log("Qwen Answer:", data.answer);
  } else {
    console.error("API Error:", data.detail);
  }
}

// Example calls
askQwen("What is ISO 27001?");
askQwen("What is STIG Baseline?");
```

---

## 🔒 Security Best Practices for Connecting Multiple Websites

> [!WARNING]
> **NEVER hardcode your secret API Key into public frontend JavaScript.**
> Anyone inspecting the website source code or network tab in DevTools can extract your key.

### Recommended Multi-Website Integration Pattern:
When connecting external websites or frontend applications to this local API:

1. **Frontend App** sends request to **Website's Backend Server** (Node.js/Express, Python/Django, Next.js API route, PHP, etc.).
2. **Website Backend Server** retrieves `QWEN_API_KEY` from its own secure environment variables.
3. **Website Backend Server** makes server-to-server call to `http://localhost:8000/v1/chat/completions` forwarding the header `X-API-Key: YOUR_API_KEY`.
4. **Website Backend Server** returns the answer back to the user's browser.

---

## 📡 API Endpoint Reference

### `GET /health`
- **Authentication**: None
- **Response 200 OK**:
  ```json
  {
    "status": "ok",
    "model": "qwen-compliance"
  }
  ```

---

### `POST /v1/chat/completions`
- **Authentication**: Required (`X-API-Key` header)
- **Request Body**:
  ```json
  {
    "message": "What is STIG Baseline?"
  }
  ```
- **Response 200 OK**:
  ```json
  {
    "success": true,
    "answer": "A STIG (Security Technical Implementation Guide) baseline is a set of cybersecurity configuration standards developed by DISA..."
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid `X-API-Key` header.
  - `400 Bad Request`: Empty or invalid `message` field.
  - `500 Internal Server Error`: Model execution exception.

---

## 🛠️ Project Structure

```text
qwen-api/
├── app/
│   ├── __init__.py       # Package marker
│   ├── main.py           # FastAPI server & route handlers
│   ├── model.py          # Model loader & inference wrapper (PyTorch/PEFT)
│   ├── auth.py           # Header API key authentication
│   └── schemas.py        # Pydantic request & response schemas
├── .env                  # Local secret configuration (API keys, paths)
├── .env.example          # Environment variable template
├── requirements.txt      # Python package dependencies
├── test_client.py        # Python script to test API endpoints
├── README.md             # Complete documentation
└── .gitignore            # Git exclusion list
```
