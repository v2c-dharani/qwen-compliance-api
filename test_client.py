import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("QWEN_API_URL", "http://localhost:10000/v1/chat")
HEALTH_URL = "http://localhost:10000/health"
API_KEY = os.getenv("QWEN_API_KEY", "qwen_secret_key_12345")

def test_health():
    print("\n--- 1. Testing GET /health ---")
    try:
        response = requests.get(HEALTH_URL)
        print("Status Code:", response.status_code)
        print("Response:", response.json())
    except Exception as e:
        print("Health check failed:", e)

def test_chat(question: str):
    print(f"\n--- Testing POST {API_URL} ---")
    print(f"Question: '{question}'")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = {
        "message": question
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        print("Status Code:", response.status_code)
        res_data = response.json()
        print("Response JSON:", res_data)
        if "response" in res_data:
            print("Extracted Response:", res_data["response"])
    except Exception as e:
        print("Chat completion request failed:", e)

if __name__ == "__main__":
    test_health()
    test_chat("What is NIST SP 800-53?")
    test_chat("What is CIS?")
    test_chat("What is ISO 27001?")
    test_chat("What is STIG Baseline?")
