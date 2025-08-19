from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import psycopg2
import os

# Get environment variables
API_KEY = os.getenv("GKEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not API_KEY:
    raise ValueError("API key not found. Set GKEY in environment variables.")
if not DATABASE_URL:
    raise ValueError("Database URL not found. Set DATABASE_URL in environment variables.")

# Initialize FastAPI
app = FastAPI()

# Configure CORS (replace "*" with your frontend URL for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-chat-canvas-01.onrender.com"],  # e.g., "https://your-frontend.onrender.com"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Define request model
class PromptRequest(BaseModel):
    prompt: str

# Store conversation messages in memory
messages = [{"role": "system", "content": "kind and informative"}]

# Connect to PostgreSQL
try:
    con = psycopg2.connect(DATABASE_URL)
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id SERIAL PRIMARY KEY,
            user_chat TEXT,
            ai_chat TEXT
        )
    """)
    con.commit()
except Exception as e:
    print("Database connection error:", e)

# Root endpoint
@app.get("/")
def root():
    return {"message": "hi"}

# Generate AI response
@app.post("/generate")
async def generate_text(request: PromptRequest):
    global con, cursor

    # Reconnect if connection closed
    if con.closed != 0:
        con = psycopg2.connect(DATABASE_URL)
        cursor = con.cursor()

    # Add user message
    messages.append({"role": "user", "content": request.prompt})

    # Call OpenAI
    chat = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages
    )
    
    reply = chat.choices[0].message.content.replace("\n", " ")
    messages.append({"role": "assistant", "content": reply})

    # Store in database
    cursor.execute(
        "INSERT INTO chat (user_chat, ai_chat) VALUES (%s, %s)",
        (request.prompt, reply)
    )
    con.commit()

    return {"reply": reply}
