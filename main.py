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

logger = logging.getLogger("guitarps")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="GuitarPS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Config ----------
JWT_SECRET = os.getenv("JWT_SECRET", "guitarps-fallback-secret-key-32chars")
JWT_ALGORITHM = "HS256"
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")

# OpenAI client configured for AvalAI
client = OpenAI(api_key=AVALAI_API_KEY, base_url=AVALAI_BASE_URL)

security = HTTPBearer()

DB_PATH = "guitarps.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guitarps_phone_users (
            phone TEXT PRIMARY KEY,
            success_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guitarps_otps (
            phone TEXT PRIMARY KEY,
            otp_code TEXT,
            expires_at REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Pydantic Models ----------
class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")

class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)

class AnalyzeRequest(BaseModel):
    problem: str = Field(..., min_length=3, max_length=1000)

# ---------- Auth / Token Helpers ----------
def create_access_token(phone: str) -> str:
    payload = {
        "sub": phone,
        "exp": datetime.now(timezone.utc).timestamp() + 86400 * 7 # 7 days
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        phone = payload.get("sub")
        if not phone:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    conn = get_db()
    row = conn.execute(
        "SELECT phone, success_count FROM guitarps_phone_users WHERE phone = ?",
        (phone,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return phone


# ---------- Routes ----------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "GuitarPS Backend is running smoothly!"}

@app.post("/api/auth/otp/request")
def request_otp(data: OTPRequest):
    phone = data.phone
    code = f"{secrets.randbelow(900000) + 100000}" # 6 digit OTP
    expires_at = time.time() + 300 # 5 minutes valid

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO guitarps_otps (phone, otp_code, expires_at) VALUES (?, ?, ?)",
        (phone, code, expires_at)
    )
    conn.commit()
    conn.close()

    # در فاز اول، کد لاگ می‌شود تا از پنل لاگ لیارا قابل مشاهده باشد
    logger.info(f"OTP for {phone}: {code}")
    
    return {"status": "success", "message": "OTP sent successfully", "debug_code": code}

@app.post("/api/auth/otp/verify")
def verify_otp(data: OTPVerify):
    phone = data.phone
    code = data.code

    conn = get_db()
    row = conn.execute(
        "SELECT otp_code, expires_at FROM guitarps_otps WHERE phone = ?",
        (phone,),
    ).fetchone()

    if not row or row["otp_code"] != code or time.time() > row["expires_at"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code")

    conn.execute("DELETE FROM guitarps_otps WHERE phone = ?", (phone,))
    
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO guitarps_phone_users (phone, success_count, created_at) VALUES (?, 0, ?)",
        (phone, now),
    )
    conn.commit()
    conn.close()

    token = create_access_token(phone)
    return {"status": "success", "access_token": token, "token_type": "bearer"}

@app.post("/api/analyze")
def analyze_guitar_problem(data: AnalyzeRequest, phone: str = Depends(get_current_user)):
    conn = get_db()
    row = conn.execute(
        "SELECT success_count FROM guitarps_phone_users WHERE phone = ?",
        (phone,),
    ).fetchone()

    success_count = row["success_count"] if row else 0
    if success_count >= 3:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="شما به سقف ۳ تحلیل موفق رایگان در فاز اول رسیده‌اید."
        )
    conn.close()

    prompt = f"""
شما یک استاد متخصص و دلسوز گیتار هستید که به هنرجویان مبتدی کمک می‌کنید.
مشکل هنرجو: "{data.problem}"

پاسخ را دقیقاً در ۳ بخش با قالب زیر بنویسید:
۱. **توضیح مشکل:** دلیل فیزیکی یا تکنیکی بروز این مشکل به زبان ساده.
۲. **تمرین عملی:** یک تمرین مشخص و گام‌به‌گام با مدت زمان تمرین روزانه برای حل مشکل.
۳. **ابزار مرتبط با لینک معتبر:** متناسب با مشکل یکی از این ابزارها را با لینک معتبر پیشنهاد بده:
- تیونر آنلاین: https://tuner.ninja
- مترونوم آنلاین: https://metronome-online.com
- دیاگرام آکوردها و گیتار: https://www.ultimate-guitar.com
از ایجاد لینک‌های ناشناخته پرهیز کن و حتماً یکی از لینک‌های معتبر بالا را در متن بیاور.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert guitar teacher helping beginners."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        ai_analysis = response.choices[0].message.content
    except Exception as e:
        logger.error(f"AvalAI error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"خطا در ارتباط با سرویس هوش مصنوعی: {str(e)}")

    conn = get_db()
    conn.execute(
        "UPDATE guitarps_phone_users SET success_count = success_count + 1 WHERE phone = ?",
        (phone,),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "remaining_analyses": 2 - success_count,
        "result": ai_analysis
    }
