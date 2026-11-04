from fastapi import FastAPI

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
