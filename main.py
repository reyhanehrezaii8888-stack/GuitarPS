import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from database import engine, get_db


logger = logging.getLogger(__name__)
app = FastAPI(title="GuitarPS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://reyhanehrezaii8888-stack.github.io",
        "https://app.guitarreyhane.ir",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer = HTTPBearer(auto_error=False)

OTP_EXPIRY = timedelta(minutes=5)
OTP_COOLDOWN = timedelta(seconds=60)
OTP_MAX_ATTEMPTS = 5
TOKEN_EXPIRY = timedelta(hours=24)


# این تابع در مدل‌های فعلی پروژه وجود دارد و زمان سازگار با SQLite تولید می‌کند.
def now_utc() -> datetime:
    return models.utc_now()


def get_jwt_secret() -> str:
    value = os.getenv("JWT_SECRET", "").strip()
    if len(value) < 32:
        raise HTTPException(
            status_code=503,
            detail="JWT_SECRET در متغیرهای محیطی تنظیم نشده یا کوتاه است.",
        )
    return value


def normalize_phone(value: str) -> str:
    phone = value.strip().replace(" ", "").replace("-", "")

    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("0098"):
        phone = "0" + phone[4:]
    elif phone.startswith("98"):
        phone = "0" + phone[2:]

    if not re.fullmatch(r"09[0-9]{9}", phone):
        raise HTTPException(
            status_code=422,
            detail="شماره موبایل باید در قالب 09123456789 باشد.",
        )
    return phone


def password_hash(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raise HTTPException(
            status_code=422,
            detail="طول رمز عبور نباید از ۷۲ بایت بیشتر باشد.",
        )
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def password_matches(password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def make_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + TOKEN_EXPIRY
    return jwt.encode(
        {"sub": subject, "exp": expires},
        get_jwt_secret(),
        algorithm="HS256",
    )


def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> str:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="ورود معتبر نیست یا منقضی شده است.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise invalid

    try:
        payload = jwt.decode(
            credentials.credentials,
            get_jwt_secret(),
            algorithms=["HS256"],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise invalid

        kind, number = subject.split(":", 1)
        if not number.isdigit():
            raise invalid

        record_id = int(number)
        if kind == "user":
            record = db.get(models.User, record_id)
        elif kind == "lead":
            record = db.get(models.PhoneLead, record_id)
            if record is not None and record.verified_at is None:
                raise invalid
        else:
            raise invalid

        if record is None:
            raise invalid

        return subject
    except (JWTError, ValueError):
        raise invalid


def otp_digest(phone: str, code: str) -> str:
    return hmac.new(
        get_jwt_secret().encode("utf-8"),
        f"{phone}:{code}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    phone: str | None
    created_at: datetime


class EmailLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpRequest(BaseModel):
    phone: str


class OtpVerify(BaseModel):
    phone: str
    code: str


class AnalyzeRequest(BaseModel):
    problem: str = Field(min_length=10, max_length=1000)


# با تنظیم دیسک دائمی /data در liara.json فعلی سازگار است.
models.Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "GuitarPS Backend is running smoothly!",
    }


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


@app.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    email = str(user.email).strip().lower()
    phone = normalize_phone(user.phone) if user.phone else None

    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="این ایمیل قبلاً ثبت شده است.")

    if phone and db.query(models.User).filter(models.User.phone == phone).first():
        raise HTTPException(status_code=409, detail="این شماره قبلاً ثبت شده است.")

    new_user = models.User(
        email=email,
        hashed_password=password_hash(user.password),
        phone=phone,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="ایمیل یا شماره موبایل تکراری است.",
        )

    return new_user


@app.post("/login", response_model=TokenOut)
def login_with_email(data: EmailLogin, db: Session = Depends(get_db)):
    # پیش از بررسی رمز، مطمئن می‌شویم قابلیت صدور توکن فعال است.
    get_jwt_secret()

    email = str(data.email).strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None or not password_matches(
        data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="ایمیل یا رمز عبور نادرست است.",
        )

    return TokenOut(access_token=make_token(f"user:{user.id}"))


@app.post("/api/send-otp")
def send_otp(data: OtpRequest, db: Session = Depends(get_db)):
    phone = normalize_phone(data.phone)
    get_jwt_secret()

    sms_key = os.getenv("SMS_API_KEY", "").strip()
    template_raw = os.getenv("SMS_TEMPLATE_ID", "").strip()
    parameter_name = os.getenv("SMS_CODE_PARAM", "Code").strip()

    if not sms_key or not template_raw or not template_raw.isdigit():
        raise HTTPException(
            status_code=503,
            detail="ارسال پیامک هنوز تنظیم یا فعال نشده است.",
        )

    if not parameter_name:
        raise HTTPException(
            status_code=503,
            detail="نام متغیر قالب پیامک تنظیم نشده است.",
        )

    current = now_utc()
    challenge = (
        db.query(models.OtpChallenge)
        .filter(models.OtpChallenge.phone == phone)
        .first()
    )

    if challenge and challenge.expires_at > current:
        if challenge.attempts >= OTP_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail="تلاش‌های مجاز تمام شده؛ پس از انقضای کد دوباره درخواست دهید.",
            )

        elapsed = current - challenge.sent_at
        if elapsed < OTP_COOLDOWN:
            wait = max(1, int((OTP_COOLDOWN - elapsed).total_seconds()) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"برای ارسال مجدد {wait} ثانیه صبر کنید.",
            )

    code = f"{secrets.randbelow(900000) + 100000}"

    try:
        response = httpx.post(
            "https://api.sms.ir/v1/send/verify",
            headers={"X-API-KEY": sms_key},
            json={
                "mobile": phone,
                "templateId": int(template_raw),
                "parameters": [
                    {"name": parameter_name, "value": code}
                ],
            },
            timeout=15.0,
        )
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("SMS.ir request failed")
        raise HTTPException(
            status_code=502,
            detail="ارسال پیامک انجام نشد؛ تنظیمات یا وضعیت سرویس را بررسی کنید.",
        )

    if str(result.get("status")) != "1":
        logger.warning("SMS.ir rejected OTP request: %s", result.get("status"))
        raise HTTPException(
            status_code=502,
            detail="سرویس پیامک درخواست را نپذیرفت؛ وضعیت قالب را بررسی کنید.",
        )

    if challenge is None:
        challenge = models.OtpChallenge(phone=phone)
        db.add(challenge)

    challenge.code_hash = otp_digest(phone, code)
    challenge.sent_at = current
    challenge.expires_at = current + OTP_EXPIRY
    challenge.attempts = 0
    db.commit()

    return {"status": "sent", "retry_after": 60}


@app.post("/api/verify-otp", response_model=TokenOut)
def verify_otp(data: OtpVerify, db: Session = Depends(get_db)):
    phone = normalize_phone(data.phone)
    code = data.code.strip()

    if not re.fullmatch(r"[0-9]{6}", code):
        raise HTTPException(status_code=400, detail="کد تأیید نامعتبر است.")

    challenge = (
        db.query(models.OtpChallenge)
        .filter(models.OtpChallenge.phone == phone)
        .first()
    )

    if challenge is None:
        raise HTTPException(
            status_code=400,
            detail="ابتدا درخواست ارسال کد بدهید.",
        )

    current = now_utc()
    if current >= challenge.expires_at:
        db.delete(challenge)
        db.commit()
        raise HTTPException(status_code=400, detail="کد تأیید منقضی شده است.")

    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="تعداد تلاش‌های مجاز تمام شده است.",
        )

    if not hmac.compare_digest(
        challenge.code_hash, otp_digest(phone, code)
    ):
        challenge.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="کد تأیید نادرست است.")

    lead = (
        db.query(models.PhoneLead)
        .filter(models.PhoneLead.phone == phone)
        .first()
    )
    if lead is None:
        lead = models.PhoneLead(phone=phone, verified_at=current)
        db.add(lead)
    else:
        lead.verified_at = current

    db.delete(challenge)
    db.commit()
    db.refresh(lead)

    return TokenOut(access_token=make_token(f"lead:{lead.id}"))


@app.post("/api/analyze")
def analyze_problem(
    data: AnalyzeRequest,
    identity: str = Depends(get_current_identity),
):
    # تا پیش از پیاده‌سازی سهمیه و اشتراک، هزینهٔ API را باز نمی‌گذاریم.
    if os.getenv("AI_ENABLED", "").lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="تحلیل هوشمند هنوز فعال نشده است.",
        )

    api_key = os.getenv("AVALAI_API_KEY", "").strip()
    model_name = os.getenv("AVALAI_MODEL", "").strip()

    if not api_key or not model_name:
        raise HTTPException(
            status_code=503,
            detail="کلید AvalAI یا نام مدل تنظیم نشده است.",
        )

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.avalai.ir/v1",
            timeout=25.0,
            max_retries=1,
        )
        result = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "تو راهنمای آموزشی گیتار برای هنرجوی مبتدی هستی. "
                        "مشکل کاربر را به فارسی و مختصر تحلیل کن، "
                        ".همچنین به شخص بگو چطور از ابزار برای رفع نیازش استفاده کند.چند گام عملی پیشنهاد بده و ابزار (اپلیکیشن یا سایت مرتبط) و تمرین مرتبط را معرفی کن."
                    ),
                },
                {"role": "user", "content": data.problem},
            ],
        )
        answer = result.choices[0].message.content
    except Exception:
        logger.exception("AvalAI analysis failed")
        raise HTTPException(
            status_code=502,
            detail="در حال حاضر تحلیل هوشمند در دسترس نیست.",
        )

    if not answer:
        raise HTTPException(
            status_code=502,
            detail="پاسخ معتبری از سرویس تحلیل دریافت نشد.",
        )

    return {"analysis": answer}
