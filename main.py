import os
import re
import secrets
import hmac
import hashlib
import logging
import sqlite3
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI
import jwt
from database import engine

logger = logging.getLogger("guitarps")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="GuitarPS Backend")

# ---------- Config ----------
JWT_SECRET = os.getenv("JWT_SECRET", "this-is-an-insecure-dev-secret-change-me-please-123456789")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET تنظیم نشده یا کوتاه است؛ یک مقدار تصادفی حداقل ۳۲ کاراکتری تنظیم کن.")

DB_PATH = engine.url.database

OTP_MODE = os.getenv("OTP_MODE", "disabled")
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY")
AVALAI_MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")
APPTIME = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))

allowed_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
if not allowed_origins:
    allowed_origins = [
        "https://reyhanehrezaii8888-stack.github.io",
        "https://app.guitarreyhane.ir",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)

bearer_scheme = HTTPBearer(auto_error=False)

ai_client = None
if AVALAI_API_KEY:
    ai_client = OpenAI(
        api_key=AVALAI_API_KEY,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.avalai.ir/v1"),
        timeout=30.0,
    )

# ---------- Database schema (only what phase 1 needs) ----------
SCHEMA = """
CREATE TABLE IF NOT EXISTS guitarps_phone_users (
    phone TEXT PRIMARY KEY,
    success_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS guitarps_otps (
    phone TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    sent_at INTEGER NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    window_start INTEGER NOT NULL,
    sent_in_window INTEGER NOT NULL DEFAULT 0
);
"""


def init_db():
    if not DB_PATH or DB_PATH == ":memory:":
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


init_db()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Helpers ----------
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_phone(raw: str) -> str:
    if not raw:
        raise HTTPException(status_code=400, detail="شماره موبایل را وارد کن.")
    s = str(raw).strip().translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)
    if s.startswith("+98"):
        s = "0" + s[3:]
    elif s.startswith("0098"):
        s = "0" + s[4:]
    elif s.startswith("98") and len(s) == 12 and s.startswith("989"):
        s = "0" + s[2:]
    if re.fullmatch(r"09\d{9}", s):
        return s
    raise HTTPException(status_code=400, detail="شماره موبایل را به شکل 09123456789 وارد کن.")


def otp_hash(phone: str, code: str) -> str:
    return hmac.new(
        JWT_SECRET.encode(), f"guitarps-otp:{phone}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def create_jwt(phone: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "phone:" + phone,
            "iat": now,
            "exp": now + int(os.getenv("JWT_EXPIRY_SECONDS", "604800")),
        },
        JWT_SECRET,
        algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="ابتدا وارد حساب کاربری شو."
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده، دوباره وارد شو.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")
    sub = payload.get("sub", "")
    if not sub.startswith("phone:"):
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")
    phone = sub.removeprefix("phone:")
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT phone, success_count FROM guitarps_phone_users WHERE phone = ?",
            (phone,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد.")
    return {"phone": row["phone"], "success_count": row["success_count"]}


# ---------- Schemas ----------
class PhoneInput(BaseModel):
    phone: str = Field(..., description="شماره موبایل به فرم 09123456789")

    @field_validator("phone")
    @classmethod
    def _norm(cls, v):
        return v


class VerifyInput(PhoneInput):
    code: str = Field(..., min_length=6, max_length=6)


class ProblemInput(BaseModel):
    problem: str = Field(..., min_length=3, max_length=3000)


# ---------- Routes ----------
@app.get("/")
def read_root():
    return {"message": "GuitarPS Backend is running smoothly!"}


@app.get("/health")
def health():
    try:
        conn = get_conn()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        raise HTTPException(status_code=503, detail="اتصال به دیتابیس برقرار نیست.")
    return {"status": "healthy"}


@app.post("/register", status_code=200)
@app.post("/api/auth/otp/request", status_code=200)
def request_otp(data: PhoneInput):
    phone = normalize_phone(data.phone)
    if OTP_MODE != "log":
        raise HTTPException(
            status_code=503, detail="روش ارسال OTP هنوز تنظیم نشده است."
        )
    now = int(time.time())
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT sent_at, sent_in_window, window_start FROM guitarps_otps WHERE phone = ?",
            (phone,),
        ).fetchone()
        if row:
            if now - row["sent_at"] < 60:
                raise HTTPException(
                    status_code=429, detail="برای دریافت کد جدید، یک دقیقه صبر کن."
                )
            window_start = row["window_start"]
            sent_in_window = row["sent_in_window"]
            if now - window_start >= 3600:
                window_start = now
                sent_in_window = 0
            if sent_in_window >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="تعداد درخواست‌های این شماره بیش از حد مجاز است.",
                )
        else:
            window_start = now
            sent_in_window = 0

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = now + APPTIME
        conn.execute(
            """
            INSERT OR REPLACE INTO guitarps_otps
            (phone, code_hash, expires_at, sent_at, attempts, window_start, sent_in_window)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """,
            (phone, otp_hash(phone, code), expires_at, now, window_start, sent_in_window + 1),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        logger.exception("Failed to record OTP")
        raise HTTPException(status_code=500, detail="خطا در ثبت کد تأیید.")
    finally:
        conn.close()

    logger.warning("TEST OTP for phone ending %s: %s", phone[-4:], code)
    return {"message": "کد تست در لاگ سرور ثبت شد.", "expires_in": APPTIME}


@app.post("/api/auth/otp/verify")
def verify_otp(data: VerifyInput):
    phone = normalize_phone(data.phone)
    now = int(time.time())
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT code_hash, expires_at, attempts FROM guitarps_otps WHERE phone = ?",
            (phone,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=400, detail="ابتدا درخواست کد بده.")
        if now > row["expires_at"]:
            conn.execute("DELETE FROM guitarps_otps WHERE phone = ?", (phone,))
            conn.commit()
            raise HTTPException(status_code=400, detail="کد منقضی شده است.")
        if row["attempts"] >= 5:
            conn.execute("DELETE FROM guitarps_otps WHERE phone = ?", (phone,))
            conn.commit()
            raise HTTPException(status_code=429, detail="تلاش‌های ناموفق بیش از حد مجاز بود؛ دوباره کد بگیر.")

        if not hmac.compare_digest(row["code_hash"], otp_hash(phone, data.code)):
            conn.execute(
                "UPDATE guitarps_otps SET attempts = attempts + 1 WHERE phone = ?",
                (phone,),
            )
            conn.commit()
            raise HTTPException(status_code=400, detail="کد اشتباه است.")

        conn.execute("DELETE FROM guitarps_otps WHERE phone = ?", (phone,))
        conn.execute(
            "INSERT OR IGNORE INTO guitarps_phone_users (phone, success_count, created_at) VALUES (?, 0, ?)",
            (phone, now),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        logger.exception("OTP verify failed")
        raise HTTPException(status_code=500, detail="خطا در تأیید کد.")
    finally:
        conn.close()

    return {"access_token": create_jwt(phone), "token_type": "bearer", "phone": phone}


ALLOWED_TOOLS = {
    "tuner": {"name": "تیونر آنلاین گیتار (Fender)", "url": "https://www.fender.com/online-guitar-tuner/"},
    "metronome": {"name": "مترونوم آنلاین (JustinGuitar)", "url": "https://www.justinguitar.com/metronome"},
    "guitar": {"name": "ابزار گیتار آنلاین (Musicca)", "url": "https://www.musicca.com/guitar"},
}


def parse_ai_answer(raw: str):
    try:
        import json as _json
        obj = _json.loads(raw)
    except Exception:
        raise HTTPException(status_code=502, detail="پاسخ هوش مصنوعی قابل خواندن نبود.")
    analysis = str(obj.get("analysis", "")).strip()
    exercise = str(obj.get("exercise", "")).strip()
    tool_key = str(obj.get("tool_key", "")).strip()
    if not analysis or not exercise:
        raise HTTPException(status_code=502, detail="پاسخ هوش مصنوعی ناقص بود.")
    if tool_key not in ALLOWED_TOOLS:
        tool_key = "guitar"
    return analysis, exercise, ALLOWED_TOOLS[tool_key]


SYSTEM_PROMPT = (
    "تو راهنمای آموزشی گیتار برای هنرجوی مبتدی هستی. "
    "خروجی را فقط به صورت JSON معتبر برگردان با این کلیدها: "
    "analysis (توضیح مشکل به زبان ساده فارسی)، exercise (یک تمرین عملی مشخص و کاربردی به فارسی)، "
    "tool_key (فقط یکی از این سه مقدار: tuner یا metronome یا guitar، متناسب با مشکل)."
)


@app.post("/api/analyze")
def analyze(problem_data: ProblemInput, user: dict = Depends(get_current_user)):
    if ai_client is None:
        raise HTTPException(status_code=503, detail="کلید هوش مصنوعی تنظیم نشده است.")

    phone = user["phone"]
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT success_count FROM guitarps_phone_users WHERE phone = ?",
            (phone,),
        ).fetchone()
        success_count = row["success_count"] if row else 0
        if success_count >= 3:
            raise HTTPException(
                status_code=429, detail="سقف ۳ تحلیل موفق برای این شماره تمام شده است."
            )
        try:
            response = ai_client.chat.completions.create(
                model=AVALAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": problem_data.problem},
                ],
                temperature=0.7,
            )
            answer = response.choices[0].message.content
            analysis, exercise, tool = parse_ai_answer(answer)
        except HTTPException:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            logger.exception("AI call failed")
            raise HTTPException(status_code=502, detail="خطا در ارتباط با سرویس هوش مصنوعی.")

        conn.execute(
            "UPDATE guitarps_phone_users SET success_count = success_count + 1 WHERE phone = ?",
            (phone,),
        )
        conn.execute("DELETE FROM guitarps_otps WHERE phone = ?", (phone,))
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        logger.exception("Analyze failed")
        raise HTTPException(status_code=500, detail="خطا در فرآیند تحلیل.")
    finally:
        conn.close()

    return {
        "analysis": analysis,
        "exercise": exercise,
        "tool": {"name": tool["name"], "url": tool["url"]},
        "remaining_uses": 3 - (success_count + 1),
    }
