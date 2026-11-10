from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


def utc_now():
    """زمان استاندارد UTC بدون تایم‌زون برای سازگاری کامل با SQLite"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)     # شماره تلفن
    email = Column(String, unique=True, index=True, nullable=False)    # ایمیل کاربر
    hashed_password = Column(String, nullable=False)                   # رمز عبور هش‌شده
    created_at = Column(DateTime, default=utc_now)                    # زمان ثبت‌نام


class OtpChallenge(Base):
    """جدول ذخیره امن و موقت کدهای تایید ارسالی برای جلوگیری از اسپم و اتک"""
    __tablename__ = "otp_challenges"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)   # شماره موبایل
    code_hash = Column(String, nullable=False)                         # هش امن کد (کد خام ذخیره نمی‌شود)
    expires_at = Column(DateTime, nullable=False)                      # زمان انقضا (۵ دقیقه)
    sent_at = Column(DateTime, nullable=False)                         # زمان ارسال (برای اعمال کول‌داون ۶۰ ثانیه‌ای)
    attempts = Column(Integer, default=0, nullable=False)              # تعداد دفعات ورود اشتباه

class PhoneLead(Base):
    __tablename__ = "phone_leads"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    verified_at = Column(DateTime, nullable=False)
