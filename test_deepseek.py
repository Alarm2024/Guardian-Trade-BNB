import os
import requests

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not DEEPSEEK_KEY:
    print("DEEPSEEK_API_KEY not set.")
    exit(1)

print("Testing DeepSeek API...")
try:
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
