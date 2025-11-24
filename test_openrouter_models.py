import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:8501",
    "X-Title": "Visual Storyteller"
}

# Test different model names
models_to_test = [
    "google/gemini-2.5-flash",
    "google/gemini-2.0-flash-001", 
    "google/gemini-flash-1.5",
    "google/gemini-pro"
]

for model in models_to_test:
    print(f"\nTesting model: {model}")
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'OK'"}
        ]
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ {model} WORKS!")
        else:
            print(f"❌ {model} failed: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ {model} error: {e}")
