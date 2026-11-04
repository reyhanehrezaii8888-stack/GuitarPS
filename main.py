from fastapi import FastAPI

app = FastAPI(title="GuitarPS API")


@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "GuitarPS Backend is running smoothly!",
    }
