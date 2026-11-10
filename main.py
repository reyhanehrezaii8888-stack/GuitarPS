import os
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from openai import OpenAI

import models
from database import engine, get_db

# ساخت خودکار جدول‌ها در دیتابیس
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuitarPS Backend")

# تنظیمات کلاینت هوش مصنوعی (AvalAI)
avalai_key = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if avalai_key:
    client = OpenAI(
        api_key=avalai_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.avalai.ir/v1")
    )
else:
    client = None

# تنظیمات پیامک SMS.ir
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_TEMPLATE_ID = int(os.getenv("SMS_TEMPLATE_ID", "0"))

# تنظیمات هش کردن پسورد
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# مدل‌های ورودی و خروجی ثبت‌نام
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    phone: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

# مسیرهای تست و بررسی سلامت سرور
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "GuitarPS Backend is running smoothly!"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# اندپوینت ثبت‌نام کاربر
@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # بررسی وجود ایمیل تکراری
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ایمیل وارد شده قبلاً ثبت شده است."
        )

    # هش کردن رمز عبور و ساخت کاربر جدید
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pwd,
        phone=user.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
