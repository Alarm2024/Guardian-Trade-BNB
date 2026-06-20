import os
import sys
import re
import requests
import base64
import getpass
from google import genai
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Usage: python3 pro_shot.py "src/File.sol" "Question"

if len(sys.argv) < 3:
    print("Usage: python3 pro_shot.py 'path/to/file' 'Your question'")
    exit(1)

# --- Security: Encrypted History Setup ---
def get_fernet_key(passphrase):
    salt = b'\x17\x8e\x1c\x9b\x01\x92\x83\x04'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

history_file = Path("/home/wyndhamdesert/.pro_shot_history.enc")
passphrase = getpass.getpass("Enter passphrase for secure history (or leave blank to skip): ")
fernet = Fernet(get_fernet_key(passphrase)) if passphrase else None

def log_to_history(q, a):
    if fernet:
        data = f"Q: {q}\nA: {a}\n---\n"
        encrypted = fernet.encrypt(data.encode())
        with open(history_file, "ab") as f:
            f.write(encrypted + b"\n")

# --- Mood-Based Styling (ANSI Colors) ---
def style_response(text):
    if "error" in text.lower(): return f"\033[93m{text}\033[0m" # Yellow
    if "```" in text: return f"\033[96m{text}\033[0m"         # Cyan
    return f"\033[92m{text}\033[0m"                           # Green

file_path = Path(sys.argv[1])
question = sys.argv[2]
context = f"\n\n[Context: {file_path.name}]\n{file_path.read_text()}" if file_path.exists() else ""
SANDBOX = Path("/home/wyndhamdesert/sandbox")

# Detect Model
deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
gemini_key = os.environ.get("GEMINI_API_KEY")

def save_to_sandbox(text):
    code_blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", text)
    for i, code in enumerate(code_blocks):
        sandbox_file = SANDBOX / f"generated_{i}.txt"
        sandbox_file.write_text(code)
        print(f"\n\033[95m[Sandbox] Code block saved to: {sandbox_file}\033[0m")

try:
    response_text = ""
    if deepseek_key:
        print("\033[94mUsing DeepSeek...\033[0m")
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {deepseek_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": f"{context}\n\nQuestion: {question}"}]
            }
        )
        response_text = response.json()['choices'][0]['message']['content']
    elif gemini_key:
        print("\033[94mUsing Google Gemini...\033[0m")
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{context}\n\nQuestion: {question}"
        )
        response_text = response.text
    else:
        print("Error: Neither GEMINI_API_KEY nor DEEPSEEK_API_KEY is set.")
        exit(1)

    print("\n--- Response ---")
    print(style_response(response_text))
    save_to_sandbox(response_text)
    log_to_history(question, response_text)
except Exception as e:
    print(f"API Error: {str(e)}")
