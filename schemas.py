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
