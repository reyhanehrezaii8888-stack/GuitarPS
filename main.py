import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# مقداردهی کلاینت با خواندن مستقیم متغیر AVALAI_API_KEY و بیس‌ارل AvalAI
api_key = os.getenv("AVALAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.avalai.ir/v1"  # آدرس استاندارد سرویس AvalAI
)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "GuitarPS Backend is running successfully!"}

@app.post("/chat")
def chat_with_ai(request: PromptRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="AVALAI_API_KEY is not set in environment variables.")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # یا مدل دلخواه شما در AvalAI
            messages=[
                {"role": "system", "content": "You are an expert guitar teaching assistant."},
                {"role": "user", "content": request.prompt}
            ]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
