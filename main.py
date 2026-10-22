import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="GuitarPS AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("AVALAI_API_KEY")

class ChatRequest(BaseModel):
    message: str
    user_level: str = "مبتدی"


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "GuitarPS API is running successfully!",
    }


@app.post("/api/chat")
def guitar_coach_chat(req: ChatRequest):
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="متغیر AVALAI_API_KEY در تنظیمات لیارا تنظیم نشده است.",
        )

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.avalai.ir/v1",
        )

        system_prompt = (
            "تو مربی و دستیار تخصصی گیتار در پلتفرم GuitarPS هستی. "
            "به پرسش‌های کاربر درباره آکوردها، ریتم، تکنیک، تمرین و تئوری موسیقی پاسخ بده. "
            f"سطح نوازندگی کاربر: {req.user_level}. "
            "پاسخ‌ها را دقیق، کاربردی و متناسب با سطح او بنویس."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message},
            ],
            temperature=0.7,
            max_tokens=600,
        )

        return {"reply": response.choices[0].message.content}

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="ارتباط با سرویس هوش مصنوعی برقرار نشد. تنظیمات API را بررسی کن.",
        )
