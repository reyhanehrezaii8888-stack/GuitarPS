import os
import uvicorn
from fastapi import FastAPI
from openai import OpenAI

app = FastAPI(title="GuitarPS API", version="1.0.0")

# اتصال به ای‌پی‌آی AvalAI با استفاده از متغیر محیطی که در لیارا ذخیره کردی
client = OpenAI(
    api_key=os.environ.get("AVALAI_API_KEY"),
    base_url="https://avalai.ir/v1"
)

@app.get("/")
def read_root():
    return {"status": "success", "message": "GuitarPS API Server is running and connected!"}

@app.post("/api/chat")
def chat_with_agent(prompt: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert guitar teaching assistant for GuitarPS."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

# این بخش کمک می‌کند اگر فایل مستقیماً اجرا شد، سرور بالا بیاید
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
