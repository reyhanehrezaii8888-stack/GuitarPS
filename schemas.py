from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# فرم ثبت‌نام کاربر
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="رمز عبور باید حداقل ۸ کاراکتر باشد")
    phone: Optional[str] = None


# فرم پاسخی که به کاربر برمی‌گردانیم (بدون لو رفتن رمز عبور!)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# فرم دریافت توکن ورود (Login)
class Token(BaseModel):
    access_token: str
    token_type: str

# --- اسکیماهای ورود با پیامک (OTP) ---

class OtpRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=13, description="شماره موبایل")

class OtpResponse(BaseModel):
    status: str
    message: str
    retry_after: Optional[int] = None   # ثانیه باقی‌مانده تا مجاز شدن ارسال مجدد

class OtpVerify(BaseModel):
    phone: str = Field(..., min_length=10, max_length=13)
    code: str = Field(..., min_length=4, max_length=8)
    email: Optional[EmailStr] = None    # اگر کاربر جدید است

class OtpLoginResponse(Token):
    is_new_user: bool = False
