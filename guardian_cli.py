import os
import google.generativeai as genai
from pathlib import Path

# Configure
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY is not set.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="You are a helpful assistant. You are professional and precise."
)
SAFE_DIR = Path("./src").resolve()

def load_context():
    # Completely silent, auto-loader
    files = list(SAFE_DIR.rglob("*.sol"))
    if not files: return ""
    
    # Auto-load the first file to save user clicks/errors
    try:
        content = files[0].read_text()
        return f"\n\n[Context: {files[0].name}]\n{content}"
    except:
        return ""

print("--- Guardian CLI (Ultra Pro - Simple) ---")
context = load_context()

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']: break
        
        full_message = f"{context}\n\n{user_input}"
        response = model.generate_content(full_message)
        print(f"Gemini: {response.text}")
        
    except Exception as e:
        # Silently log error, just print a user-friendly message
        with open("/home/wyndhamdesert/.cli_error.log", "a") as f:
            f.write(str(e) + "\n")
        print("\nGemini is busy or encountered a small issue. Please try typing your question again.")
