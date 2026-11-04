import os
from dotenv import load_dotenv
from fastapi import FastAPI

# خواندن متغیرهای محیطی در صورت وجود
load_dotenv()

app = FastAPI(title="GuitarPS API")

# خواندن امن کلید (اگر نبود خطا ندهد)
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "NOT_SET")


@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "GuitarPS Backend is running smoothly!",
        "env_loaded": True,
        "api_key_configured": AVALAI_API_KEY != "NOT_SET",
    }
