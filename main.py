from fastapi.responses import FileResponse
import os
import re
import secrets
import logging
import sqlite3
import time
import requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, HTTPBasic, HTTPBasicCredentials
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

# ---------------------------------------------------------------
# تنظیمات اصلی، sms.ir و ادمین
# ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 روز

AVALAI_BASE_URL = "https://api.avalai.ir/v1"

SMS_IR_API_KEY = os.getenv("SMS_IR_API_KEY", "")
SMS_IR_TEMPLATE_ID = os.getenv("SMS_IR_TEMPLATE_ID", "")

# اطلاعات ورود به پنل ادمین (قابل تنظیم در متغیرهای محیطی لیارا)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "یک")

# ---------------------------------------------------------------
# مسیر دیتابیس SQLite
# ---------------------------------------------------------------
DB_FILE = os.getenv("DB_PATH", "/tmp/guitarps.db")
MAX_FREE_ANALYSES = 3


def get_db_connection() -> sqlite3.Connection:
    db_dir = os.path.dirname(os.path.abspath(DB_FILE))
    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError as exc:
        logger.warning("Could not create db directory %s: %s", db_dir, exc)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                used_analyses INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at REAL NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
        logger.info("Database successfully initialized at %s", DB_FILE)
    finally:
        conn.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_ai_client() -> OpenAI:
    api_key = os.getenv("AVALAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="کلید AVALAI_API_KEY در تنظیمات سرور یافت نشد",
        )
    return OpenAI(api_key=api_key, base_url=AVALAI_BASE_URL)


class OTPRequestIn(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)


class OTPVerifyIn(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    code: str = Field(..., min_length=4, max_length=8)


class AnalyzeIn(BaseModel):
    problem: str = Field(..., min_length=5, max_length=2000)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    remaining_analyses: int


security = HTTPBearer(auto_error=False)
security_basic = HTTPBasic()


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    return digits


def create_secret-75e033a7(phone: str) -> str:
    payload = {
        "sub": phone,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن احراز هویت ارسال نشده است",
        )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن منقضی شده است. لطفا مجدد وارد شوید",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
        )
    phone = payload.get("sub")
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
        )
    return phone


# تابع بررسی دسترسی ادمین
def verify_admin(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور ادمین اشتباه است",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/")
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "success", "message": "GuitarPS Backend is running smoothly!"}


# ---------------------------------------------------------------
# اندپوینت ادمین برای دیدن کاربران ثبت‌نام شده
# ---------------------------------------------------------------
@app.get("/api/admin/users")
def get_admin_users(admin: str = Depends(verify_admin)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, phone, used_analyses, created_at FROM users ORDER BY id DESC")
        rows = [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
    return {
        "status": "success",
        "total_users": len(rows),
        "users": rows
    }


@app.post("/api/auth/otp/request")
def request_otp(payload: OTPRequestIn):
    phone = normalize_phone(payload.phone)
    if len(phone) != 11 or not phone.startswith("09"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شماره موبایل وارد شده معتبر نیست",
        )

    code = f"{secrets.randbelow(90000) + 10000}"
    expires_at = time.time() + 300  # اعتبار ۵ دقیقه

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE otp_codes SET consumed = 1 WHERE phone = ? AND consumed = 0",
            (phone,),
        )
        cur.execute(
            "INSERT INTO otp_codes (phone, code, expires_at) VALUES (?, ?, ?)",
            (phone, code, expires_at),
        )
        conn.commit()
    except Exception as exc:
        logger.exception("OTP save failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در ثبت کد تایید در دیتابیس",
        )
    finally:
        conn.close()

    # ارسال واقعی پیامک از طریق sms.ir
    if SMS_IR_API_KEY and SMS_IR_TEMPLATE_ID:
        try:
            sms_url = "https://api.sms.ir/v1/send/verify"
            sms_payload = {
                "mobile": phone,
                "templateId": int(SMS_IR_TEMPLATE_ID),
                "parameters": [
                    {"name": "Code", "value": code}
                ]
            }
            sms_headers = {
                "X-API-KEY": SMS_IR_API_KEY,
                "Content-Type": "application/json"
            }
            res = requests.post(sms_url, json=sms_payload, headers=sms_headers, timeout=10)
            res_data = res.json()
            if res.status_code != 200 or not res_data.get("status"):
                logger.error("sms.ir error: %s", res.text)
        except Exception as e:
            logger.exception("Failed to send SMS via sms.ir")

    logger.info("Generated OTP for %s -> %s", phone, code)
    return {
        "status": "success",
        "message": "کد تایید با موفقیت ارسال شد",
    }


@app.post("/api/auth/otp/verify", response_model=TokenOut)
def verify_otp(payload: OTPVerifyIn):
    phone = normalize_phone(payload.phone)

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, expires_at FROM otp_codes
            WHERE phone = ? AND code = ? AND consumed = 0
            ORDER BY id DESC LIMIT 1
            """,
            (phone, payload.code),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="کد تایید اشتباه است",
            )
        if time.time() > row["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="کد تایید منقضی شده است",
            )

        cur.execute("UPDATE otp_codes SET consumed = 1 WHERE id = ?", (row["id"],))
        
        cur.execute(
            "INSERT OR IGNORE INTO users (phone, used_analyses, created_at) VALUES (?, 0, ?)",
            (phone, datetime.now(timezone.utc).isoformat()),
        )
        cur.execute("SELECT used_analyses FROM users WHERE phone = ?", (phone,))
        used = cur.fetchone()["used_analyses"]
        conn.commit()
    finally:
        conn.close()

    access_token = create_secret-75e033a7(phone)
    return TokenOut(
        access_token=access_token,
        remaining_analyses=max(0, MAX_FREE_ANALYSES - used),
    )


@app.post("/api/analyze")
def analyze_problem(payload: AnalyzeIn, phone: str = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT used_analyses FROM users WHERE phone = ?", (phone,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="کاربر در سیستم یافت نشد",
            )
        used = row["used_analyses"]
        if used >= MAX_FREE_ANALYSES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="سهمیه ۳ تحلیل رایگان شما به پایان رسیده است",
            )
    finally:
        conn.close()

    client = get_ai_client()

    system_prompt = (
        "تو یک مدرس حرفه‌ای و برجسته گیتار هستی. کاربر مشکل نوازندگی خود را مطرح می‌کند. "
        "پاسخ خود را دقیقاً و فقط در سه بخش به فارسی روان و دقیق ساختار بده:\n"
        "۱) توضیح مشکل: تحلیل ریشه فنی و بیومکانیکی مشکل در نوازندگی.\n"
        "۲) تمرین عملی: یک تمرین گام‌به‌گام و مشخص برای رفع مشکل.\n"
        "۳) ابزار مرتبط: معرفی یک ابزار استاندارد (مانند تیونر، مترونوم، نرم‌افزار آموزشی معتبر) همراه با لینک دانلود یا سایت معتبر.\n"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.problem},
            ],
            temperature=0.4,
            max_tokens=900,
        )
        answer = completion.choices[0].message.content
    except Exception as exc:
        logger.exception("AI analysis request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="خطا در ارتباط با هوش مصنوعی AvalAI. لطفا مجدد تلاش کنید",
        )

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET used_analyses = used_analyses + 1 WHERE phone = ?",
            (phone,),
        )
        cur.execute("SELECT used_analyses FROM users WHERE phone = ?", (phone,))
        used = cur.fetchone()["used_analyses"]
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "analysis": answer,
        "remaining_analyses": max(0, MAX_FREE_ANALYSES - used),
    }
