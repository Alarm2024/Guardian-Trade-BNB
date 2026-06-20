import os
import google.generativeai as genai

# 1. Load the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set.")
    exit(1)

try:
    print("Configuring Gemini...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Sending test request...")
    response = model.generate_content("Hello, are you working?")
    
    print("SUCCESS! Gemini responded:")
    print(response.text)
except Exception as e:
    print(f"FAILED: An error occurred: {e}")
