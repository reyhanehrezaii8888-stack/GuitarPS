from passlib.context import CryptContext

# تنظیمات هش کردن پسورد با الگوریتم قدرتمند bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# تابع برای قفل کردن (هش کردن) پسورد خام
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# تابع برای مقایسه پسورد موقع لاگین با پسورد ذخیره شده
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
