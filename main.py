from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import psycopg2
import os

# Load API key
load_dotenv()
key = os.getenv("GKEY")
if not key:
    raise ValueError("API key not found. Set GKEY in environment variables.")

# Load Database URL from Render
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Database URL not found. Set DATABASE_URL in environment variables.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(
    api_key=key,
    base_url="https://api.groq.com/openai/v1"
)

class PromptRequest(BaseModel):
    prompt: str

messages = [
    {"role": "system", "content": "kind and informative"}
]

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

@app.get('/')
def root():
    return {'message': 'hi'}

@app.post("/generate")
async def generate_text(request: PromptRequest):
    global con, cursor
    if con.closed:
        con = psycopg2.connect(DATABASE_URL)
        cursor = con.cursor()

    messages.append({'role': 'user', 'content': request.prompt})
    
    chat = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages
    )
    
    reply = chat.choices[0].message.content.replace("\n", " ")
    messages.append({'role': 'assistant', 'content': reply})

    cursor.execute(
        "INSERT INTO chat (user_chat, ai_chat) VALUES (%s, %s)",
        (request.prompt, reply)
    )
    con.commit()

    return {"reply": reply}
