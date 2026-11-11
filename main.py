import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    select,
    text,
    update,
    insert,
)
from sqlalchemy.orm import Session

import models
from database import engine, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ساخت جدول‌های اصلی دیتابیس
models.Base.metadata.create_all(bind=engine)

# جدول‌های فاز اول (فقط شماره‌ها، OTP، و شمارنده‌ی تحلیل‌های موفق)
mvp_metadata = MetaData()

phone_users = Table(
    "guitarps_phone_users",
    mvp_metadata,
    Column("id", Integer, primary_key=True),
    Column("phone", String(11), nullable=False, unique=True),
    Column("success_count", Integer, nullable=False, default=0),  # شمارنده برای محدودیت ۳ بار
)

otp_codes = Table(
    "guitarps_otp_codes",
    mvp_metadata,
    Column("phone", String(11), primary_key=True),
    Column("code_hash", String(64), nullable=False),
    Column("expires_at", Integer, nullable=False),
    Column("last_sent_at", Integer, nullable=False),
    Column("window_start", Integer, nullable=False),
    Column("window_count", Integer, nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("consumed", Integer, nullable=False),
)

mvp_metadata.create_all(bind=engine)

JWT_SECRET = os.getenv("JWT_SECRET", "")
if len(JWT_SECRET) < 32:
    raise RuntimeError(
        "JWT_SECRET تنظیم نشده یا کوتاه است؛ یک مقدار تصادفی حداقل ۳۲ کاراکتری تنظیم کن."
    )

OTP_MODE = os.getenv("OTP_MODE", "disabled").strip().lower()
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "").strip()
AVALAI_MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")

ai_client = (
    OpenAI(
        api_key=AVALAI_API_KEY,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.avalai.ir/v1"),
        timeout=30.0,
    )
    if AVALAI_API_KEY
    else None
)

app = FastAPI(title="GuitarPS Backend")

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://reyhanehrezaii8888-stack.github.io",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer_scheme = HTTPBearer(auto_error=False)


def normalize_phone(value: str) -> str:
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"

    value = value.translate(
        str.maketrans(
            persian_digits + arabic_digits,
            english_digits + english_digits,
        )
    )
    value = value.strip().replace(" ", "").replace("-", "")

    if value.startswith("+98"):
        value = "0" + value[3:]
    elif value.startswith("0098"):
        value = "0" + value[4:]
    elif value.startswith("98"):
        value = "0" + value[2:]

    if not re.fullmatch(r"09\d{9}", value):
        raise ValueError("شماره موبایل را به شکل 09123456789 وارد کن.")

    return value


def otp_hash(phone: str, code: str) -> str:
    message = f"guitarps-otp:{phone}:{code}".encode("utf-8")
    return hmac.new(
        JWT_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


class PhoneInput(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class VerifyInput(PhoneInput):
    code: str = Field(min_length=6, max_length=6)


class ProblemInput(BaseModel):
    problem: str = Field(min_length=3, max_length=3000)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="ابتدا وارد حساب کاربری شو.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise error

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        subject = payload["sub"]

        if not isinstance(subject, str) or not subject.startswith("phone:"):
            raise error

        user_id = int(subject.removeprefix("phone:"))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error

    user = db.execute(
        select(phone_users.c.id, phone_users.c.phone, phone_users.c.success_count).where(
            phone_users.c.id == user_id
        )
    ).mappings().first()

    if user is None:
        raise error

    return user


@app.get("/")
def read_root():
    return {"message": "GuitarPS Backend is running smoothly!"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="اتصال به دیتابیس برقرار نیست.",
        )

    return {"status": "healthy"}


@app.post("/api/auth/otp/request")
def request_otp(data: PhoneInput, db: Session = Depends(get_db)):
    if OTP_MODE != "log":
        raise HTTPException(
            status_code=503,
            detail="روش ارسال OTP هنوز تنظیم نشده است.",
        )

    now = int(time.time())
    existing = db.execute(
        select(otp_codes).where(otp_codes.c.phone == data.phone)
    ).mappings().first()

    if existing and now - existing["last_sent_at"] < 60:
        raise HTTPException(
            status_code=429,
            detail="برای دریافت کد جدید، یک دقیقه صبر کن.",
        )

    if existing and now - existing["window_start"] < 3600:
        window_start = existing["window_start"]
        window_count = existing["window_count"]

        if window_count >= 5:
            raise HTTPException(
                status_code=429,
                detail="تعداد درخواست‌های این شماره بیش از حد مجاز است.",
            )
    else:
        window_start = now
        window_count = 0

    code = f"{secrets.randbelow(1_000_000):06d}"
    values = {
        "code_hash": otp_hash(data.phone, code),
        "expires_at": now + 300,
        "last_sent_at": now,
        "window_start": window_start,
        "window_count": window_count + 1,
        "attempts": 0,
        "consumed": 0,
    }

    try:
        if existing:
            db.execute(
                update(otp_codes)
                .where(otp_codes.c.phone == data.phone)
                .values(**values)
            )
        else:
            db.execute(insert(otp_codes).values(phone=data.phone, **values))

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not store OTP")
        raise HTTPException(status_code=500, detail="خطا در ثبت کد تأیید.")

    logger.warning(
        "TEST OTP for phone ending %s: %s",
        data.phone[-4:],
        code,
    )
    return {"message": "کد تست در لاگ سرور ثبت شد.", "expires_in": 300}


@app.post("/api/auth/otp/verify")
def verify_otp(data: VerifyInput, db: Session = Depends(get_db)):
    if not re.fullmatch(r"\d{6}", data.code):
        raise HTTPException(status_code=422, detail="کد باید شش رقم باشد.")

    now = int(time.time())
    saved = db.execute(
        select(otp_codes).where(otp_codes.c.phone == data.phone)
    ).mappings().first()

    invalid = HTTPException(
        status_code=400,
        detail="کد نامعتبر، استفاده‌شده یا منقضی است.",
    )

    if (
        saved is None
        or saved["consumed"]
        or saved["attempts"] >= 5
        or saved["expires_at"] <= now
    ):
        raise invalid

    supplied_hash = otp_hash(data.phone, data.code)

    if not hmac.compare_digest(supplied_hash, saved["code_hash"]):
        db.execute(
            update(otp_codes)
            .where(
                otp_codes.c.phone == data.phone,
                otp_codes.c.consumed == 0,
                otp_codes.c.attempts < 5,
            )
            .values(attempts=otp_codes.c.attempts + 1)
        )
        db.commit()
        raise invalid

    try:
        claimed = db.execute(
            update(otp_codes)
            .where(
                otp_codes.c.phone == data.phone,
                otp_codes.c.code_hash == saved["code_hash"],
                otp_codes.c.consumed == 0,
                otp_codes.c.attempts < 5,
                otp_codes.c.expires_at > now,
            )
            .values(consumed=1)
        )

        if claimed.rowcount != 1:
            db.rollback()
            raise invalid

        user = db.execute(
            select(phone_users.c.id).where(phone_users.c.phone == data.phone)
        ).first()

        if user is None:
            db.execute(
                insert(phone_users).values(phone=data.phone, success_count=0)
            )
            user_row = db.execute(
                select(phone_users.c.id).where(phone_users.c.phone == data.phone)
            ).first()
            user_id = user_row.id
        else:
            user_id = user.id

        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("OTP verification failed")
        raise HTTPException(status_code=500, detail="خطا در ورود کاربر.")

    token = jwt.encode(
        {
            "sub": f"phone:{user_id}",
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
        },
        JWT_SECRET,
        algorithm="HS256",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
    }


@app.post("/api/analyze", status_code=200)
def analyze_problem(
    data: ProblemInput,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # بررسی محدودیت ۳ تحلیل موفق
    if user["success_count"] >= 3:
        raise HTTPException(
            status_code=403,
            detail="سهمیه‌ی ۳ تحلیل رایگان شما به پایان رسیده است.",
        )

    problem_text = data.problem.strip()
    if not problem_text:
        raise HTTPException(status_code=422, detail="متن مشکل خالی است.")

    if ai_client is None:
        raise HTTPException(
            status_code=503,
            detail="کلید AVALAI_API_KEY تنظیم نشده است.",
        )

    try:
        response = ai_client.chat.completions.create(
            model=AVALAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "تو مربی حرفه‌ای گیتار برای هنرجویان مبتدی هستی. "
                        "پاسخ خود را دقیقاً در ۳ بخش مجزا با این عنوان‌ها ارائه بده:\n"
                        "۱. تحلیل مشکل (توضیح کوتاه علت مشکل)\n"
                        "۲. تمرین عملی (یک گام تمرینی مشخص برای رفع مشکل)\n"
                        "۳. ابزار مرتبط (معرفی یک ابزار یا سایت مفید همراه با لینک معتبر آن)"
                    ),
                },
                {"role": "user", "content": problem_text},
            ],
        )

        answer = response.choices[0].message.content
        if not answer:
            raise ValueError("Empty AI response")

        # افزایش شمارنده تحلیل‌های موفق کاربر
        db.execute(
            update(phone_users)
            .where(phone_users.c.id == user["id"])
            .values(success_count=phone_users.c.success_count + 1)
        )
        db.commit()

        return {
            "success": True,
            "remaining_analyses": 3 - (user["success_count"] + 1),
            "result": answer,
        }

    except Exception:
        db.rollback()
        logger.exception("AvalAI analysis failed")
        raise HTTPException(
            status_code=502,
            detail="خطا در تحلیل هوش مصنوعی. لطفاً دوباره تلاش کنید.",
        )
