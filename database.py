import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# در لیارا مسیر /var/lib/liara/storage مسیر دائمی و مجاز برای نوشتن است
STORAGE_DIR = "/var/lib/liara/storage"
# اگر در سیستم خودت (Local) هستی، همان مسیر قبلی باشد
DB_PATH = os.path.join(STORAGE_DIR, "guitarps.db") if os.path.exists(STORAGE_DIR) else "guitarps.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
