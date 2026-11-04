from fastapi import FastAPI
import uvicorn

app = FastAPI()

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
