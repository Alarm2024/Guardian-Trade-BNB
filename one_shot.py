import os
import sys
from google import genai

if len(sys.argv) < 2:
    print("Usage: python3 one_shot.py 'Your question'")
    exit(1)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY is not set.")
    exit(1)

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=sys.argv[1]
    )
    print(response.text)
except Exception as e:
    print(f"API Error: {str(e)}")
