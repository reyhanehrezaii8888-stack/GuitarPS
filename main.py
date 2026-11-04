from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uvicorn

import models
import schemas
from database import engine, get_db
from security import get_password_hash

# دستور ساخت خودکار جدول‌ها در دیتابیس هنگام روشن شدن سرور
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuitarPS Backend")


@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "GuitarPS Backend is running smoothly!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# مسیر ثبت‌نام کاربر جدید (تسک ۳-۴)
@app.post("/api/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # بررسی تکراری نبودن ایمیل
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="این ایمیل قبلاً ثبت‌نام شده است"
        )

    # هش کردن رمز عبور
    hashed_pwd = get_password_hash(user_in.password)

    # ساخت آبجکت کاربر جدید و ذخیره در دیتابیس
    new_user = models.User(
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
