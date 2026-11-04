from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)     # شماره تلفن
    email = Column(String, unique=True, index=True, nullable=False)    # ایمیل کاربر
    hashed_password = Column(String, nullable=False)                   # رمز عبور هش‌شده
    created_at = Column(DateTime, default=datetime.utcnow)             # زمان ثبت‌نام
