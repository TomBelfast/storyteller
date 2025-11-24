import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

print(f"Testing with key: {key[:20]}...{key[-10:]}\n")

# Test request
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:8501",
    "X-Title": "Visual Storyteller"
}

payload = {
    "model": "google/gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Reply with just 'OK'"}
    ]
}

print("Sending request to OpenRouter...")
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    json=payload,
    headers=headers,
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("\n✅ SUCCESS - API Key works!")
else:
    print(f"\n❌ FAILED - {response.status_code}")
    
    # Check if maybe it's a credits issue
    if "credit" in response.text.lower() or "balance" in response.text.lower():
        print("⚠️  Possible credits/balance issue")
