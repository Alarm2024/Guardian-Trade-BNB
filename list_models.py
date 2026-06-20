import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

for m in genai.list_models():
    print(f"Model: {m.name}")
