import os
import logging
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from openai import OpenAI
import jwt

import models
from database import engine, get_db

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ساخت جدول‌ها در دیتابیس
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuitarPS Backend")

# تنظیمات CORS برای دسترسی فرانت‌اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تنظیمات هوش مصنوعی (AvalAI)
avalai_key = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = None
if avalai_key:
    client = OpenAI(
        api_key=avalai_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.avalai.ir/v1")
    )

# تنظیمات رمزنگاری پسورد
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# مدل‌های Pydantic
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str | None = None

    class Config:
        from_attributes = True

class ProblemAnalyzeRequest(BaseModel):
    problem: str

# مسیرهای بررسی سلامت سرور
@app.get("/")
def read_root():
    return {"message": "GuitarPS Backend is running smoothly!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="اتصال به دیتابیس برقرار نیست.")
    return {"status": "healthy"}

# اندپوینت ثبت‌نام کاربر
@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    email = str(user.email).strip().lower()
    
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="این ایمیل قبلاً ثبت نام کرده است.")

    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(
        email=email,
        hashed_password=hashed_pwd,
        phone=user.phone
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        logger.exception("Error during user registration")
        raise HTTPException(status_code=500, detail="خطا در ثبت‌نام کاربر.")

    return new_user

# اندپوینت تحلیل مشکل گیتار با هوش مصنوعی
@app.post("/api/analyze")
def analyze_guitar_problem(data: ProblemAnalyzeRequest):
    if not client:
        # حالت پیش‌فرض اگر کلید هوش مصنوعی ست نشده باشد
        return {
        
            "analysis": f"بررسی اولیه مشکل شما: {data.problem}",
            "steps": [
                "1. ساز را کوک کنید و وضعیت نشستن خود را بررسی کنید.",
                "2. فشار انگشت روی فرت را تنظیم کنید تا گز ندهد.",
                "3. روزانه ۱۰ دقیقه تمرین آرام و با مترونوم داشته باشید."
            ],
            "recommended_tool": "مترونوم آنلاین و تمرین کشش انگشتان"
        }

    try:
        response = client.chat.completions.create(
            model=os.getenv("AVALAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "تو راهنمای آموزشی گیتار برای هنرجوی مبتدی هستی. مشکل کاربر را به فارسی و مختصر تحلیل کن، چند گام عملی پیشنهاد بده و ابزار یا تمرین مرتبط را معرفی کن."
                },
                {"role": "user", "content": data.problem}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content
        return {"result": answer}
    except Exception as e:
        logger.exception("AI service error")
        raise HTTPException(status_code=500, detail=f"خطا در ارتباط با سرویس هوش مصنوعی: {str(e)}")
