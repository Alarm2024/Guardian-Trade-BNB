from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json
import logging
import asyncio
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini with validation
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY environment variable not set!")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="You are a helpful assistant. You support Arabic fluently. Respond in Arabic if asked in Arabic, or if instructed to do so."
)


chat_history = {}
SAFE_DIR = Path("./src").resolve()

async def call_with_backoff(func, *args, **kwargs):
    retries = 3
    delay = 1
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise e

@app.get("/files")
async def list_files():
    try:
        files = [str(f.relative_to(SAFE_DIR)) for f in SAFE_DIR.rglob("*.sol")]
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"files": []}

@app.post("/read_file")
async def read_file(request: Request):
    data = await request.json()
    filename = data.get("filename")
    try:
        file_path = (SAFE_DIR / filename).resolve()
        if not str(file_path).startswith(str(SAFE_DIR)):
            raise HTTPException(status_code=403, detail="Access denied")
        return {"content": file_path.read_text()}
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "default_user")
    message = data.get("message")
    context = data.get("context", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="No message provided")

    try:
        if user_id not in chat_history:
            chat_history[user_id] = model.start_chat(history=[])
        
        chat_session = chat_history[user_id]
        
        # Keep only the last 10 messages (5 exchanges) to save tokens
        if len(chat_session.history) > 10:
            chat_session.history = chat_session.history[-10:]
            
        full_message = f"Context: {context}\n\nQuestion: {message}" if context else message

        async def generate():
            try:
                # Use the helper to handle retries
                response = await call_with_backoff(chat_session.send_message, full_message, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                logger.error(f"Error during chat streaming: {e}")
                yield f"\n[خطأ: تجاوز الحد المسموح، يرجى المحاولة لاحقاً.]"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Chat setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear")
async def clear(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "default_user")
    if user_id in chat_history:
        del chat_history[user_id]
    return {"status": "cleared"}

app.mount("/", StaticFiles(directory="gemini_app/static", html=True), name="static")

@app.get("/")
async def read_index():
    return FileResponse("gemini_app/static/index.html")
