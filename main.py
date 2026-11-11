import os
import re
import secrets
import logging
import sqlite3
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from openai import OpenAI
import jwt
from dotenv import load_dotenv

load_dotenv()

# تنظیمات لاگینگ
logger = logging.getLogger("guitarps")
logging.basicConfig(level=logging.INFO)

# تنظیمات اتصال به AvalAI با رفع خطای Missing credentials
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")

client = OpenAI(
    api_key=AVALAI_API_KEY if AVALAI_API_KEY else "dummy-key",
    base_url=AVALAI_BASE_URL
)

# تنظیمات JWT و امنیت
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ساعت

security = HTTPBearer()

app = FastAPI(title="GuitarPS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# راه‌اندازی دیتابیس SQLite برای کاربران و تعداد تحلیل‌ها
DB_FILE = "guitars.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            otp TEXT,
            otp_expires INTEGER,
            analysis_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# مدل‌های Pydantic
class OTPRequest(BaseModel):
    phone: str = Field(..., description="شماره موبایل کاربر")

class OTPVerify(BaseModel):
    phone: str
    otp: str

class AnalyzeRequest(BaseModel):
    phone: str = Field(..., description="شماره موبایل برای بررسی سهمیه فاز اول")
    problem: str = Field(..., description="شرح مشکل نوازندگی گیتار")

def create_jwt_token(phone: str):
    expire = time.time() + (TOKEN_EXPIRE_MINUTES * 60)
    to_encode = {"sub": phone, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=401, detail="توکن نامعتبر است")
        return phone
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="احراز هویت نامعتبر یا منقضی شده است")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "GuitarPS Backend is running smoothly!"}

@app.post("/api/auth/otp/request")
def request_otp(data: OTPRequest):
    phone = data.phone.strip()
    if not re.match(r"^09\d{9}$", phone):
        raise HTTPException(status_code=400, detail="شماره موبایل نامعتبر است (مثال: 09123456789)")
    
    # تولید کد OTP ثابت ۵ رقمی برای تست یا تصادفی
    otp_code = "12345"
    expires = int(time.time()) + 300  # ۵ دقیقه اعتبار
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (phone, otp, otp_expires, analysis_count)
        VALUES (?, ?, ?, 0)
        ON CONFLICT(phone) DO UPDATE SET otp=?, otp_expires=?
    """, (phone, otp_code, expires, otp_code, expires))
    conn.commit()
    conn.close()
    
    # در محیط واقعی اینجا پیامک ارسال می‌شود؛ برای فاز اول برمی‌گردانیم تا راحت تست کنی
    return {"status": "success", "message": f"کد تایید ارسال شد (کد تست: {otp_code})", "phone": phone}

@app.post("/api/auth/otp/verify")
def verify_otp(data: OTPVerify):
    phone = data.phone.strip()
    entered_otp = data.otp.strip()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT otp, otp_expires FROM users WHERE phone=?", (phone,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد. ابتدا درخواست کد OTP کنید.")
    
    stored_otp, expires = row
    if time.time() > expires:
        raise HTTPException(status_code=400, detail="کد تایید منقضی شده است.")
    
    if stored_otp != entered_otp:
        raise HTTPException(status_code=400, detail="کد تایید اشتباه است.")
    
    token = create_jwt_token(phone)
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@app.post("/api/analyze")
def analyze_guitar_problem(data: AnalyzeRequest, phone: str = Depends(get_current_user)):
    # بررسی محدودیت ۳ تحلیل موفق برای هر شماره
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT analysis_count FROM users WHERE phone=?", (phone,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    
    analysis_count = row[0]
    if analysis_count >= 3:
        conn.close()
        raise HTTPException(status_code=403, detail="سهمیه رایگان شما (۳ تحلیل موفق) به پایان رسیده است.")
    
    try:
        # درخواست تحلیل به AvalAI طبق ساختار فاز اول (۳ بخش: توضیح مشکل، تمرین عملی، ابزار مرتبط معتبر)
        prompt = f"""
        شما یک استاد حرفه‌ای و دقیق گیتار هستید. کاربر این مشکل را مطرح کرده است: "{data.problem}"
        پاسخ خود را دقیقاً در ۳ بخش مجزا با عناوین زیر ارائه کنید:
        1. توضیح مشکل (تحلیل تخصصی علت بروز مشکل)
        2. تمرین عملی (راهکار گام‌به‌گام و تمرین مشخص برای رفع آن)
        3. ابزار مرتبط (معرفی یک ابزار معتبر مثل متونوم، تیونر یا نرم‌افزارهای استاندارد تمرین گیتار با لینک معتبر دانلود یا وبسایت رسمی آن‌ها)
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # یا مدل مدنظر آوال‌آی
            messages=[
                {"role": "system", "content": "تو یک دستیار تخصصی آموزش گیتار هستی."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        analysis_result = response.choices[0].message.content
        
        # افزایش تعداد تحلیل‌های موفق کاربر
        cursor.execute("UPDATE users SET analysis_count = analysis_count + 1 WHERE phone=?", (phone,))
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "remaining_analyses": 3 - (analysis_count + 1),
            "result": analysis_result
        }
        
    except Exception as e:
        conn.close()
        logger.error(f"Error in analyze: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطا در ارتباط با هوش مصنوعی: {str(e)}")
