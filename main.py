from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()
key = os.getenv("GKEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=key,
    base_url="https://api.groq.com/openai/v1"
)

class PromptRequest(BaseModel):
    prompt: str

messages=[
            {"role": "system", "content": "kind and informative"}
        ]
try:
    con = mysql.connector.connect(host='localhost',user='root',password='',database='test')
    if con.is_connected():
        cursor=con.cursor()
        cursor.execute("""
                create table if not exists chat(
                SNo Int Auto_increment primary key,
                user_chat text,
                ai_chat text
                )
            """)
except Exception as e:
    print(e)

@app.get('/')
def root():
    return {'message':'hi'}

@app.post("/generate")
async def generate_text(request: PromptRequest):
    messages.append({'role':'user','content':request.prompt})
    chat = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages
    )
    reply = chat.choices[0].message.content.replace("\n", " ")
    messages.append({'role':'assistant','content':reply})
    cursor.execute("insert into chat (user_chat,ai_chat) values (%s,%s)",(request.prompt,reply))
    con.commit()
    return f'{reply}'
