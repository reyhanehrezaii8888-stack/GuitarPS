from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# آدرس فایل دیتابیس محلی
SQLALCHEMY_DATABASE_URL = "sqlite:///./guitarps.db"

# ایجاد موتور دیتابیس SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# ساخت کلاس نشست‌ها (Session) برای کار با داده‌ها
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# کلاس پایه برای تعریف جدول‌های دیتابیس
Base = declarative_base()


# تابعی برای اتصال و قطع اتصال خودکار به دیتابیس در هر ریکوئست
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
