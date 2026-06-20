import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    api_key = os.getenv("GEMINI_API_KEY")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    # Initialize the client based on your environment
    if api_key and api_key != "your_gemini_api_key_here":
        print(f"[*] Authenticating via API Key...")
        client = genai.Client(api_key=api_key)
    else:
        print(f"[*] Authenticating via Vertex AI (Project: {project_id})...")
        client = genai.Client(vertexai=True, project=project_id, location='us-central1')

    print("\n--- Available Gemini Models ---")
    try:
        for model in client.models.list():
            # Filter for models that support text generation
            if 'generateContent' in model.supported_actions:
                print(f"ID: {model.name}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    list_available_models()