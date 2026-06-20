import os
import sys
from google import genai
from pathlib import Path

print("--- Running Health Check ---")

# 1. Check API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("[FAIL] GEMINI_API_KEY is not set.")
else:
    print("[PASS] GEMINI_API_KEY is set.")

# 2. Check File
file_path = Path("src/GuardianAngelCarbon.sol")
if file_path.exists():
    print("[PASS] File 'src/GuardianAngelCarbon.sol' found.")
else:
    print("[FAIL] File 'src/GuardianAngelCarbon.sol' NOT found.")

# 3. Check API Connection
if api_key:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Say 'Hello'"
        )
        print("[PASS] Successfully connected to Gemini API.")
    except Exception as e:
        print(f"[FAIL] Could not connect to API. Error: {str(e)}")
else:
    print("[SKIP] Cannot test API connection without key.")

print("--- Check Complete ---")
