from fastapi import FastAPI
from database import create_tables

app = FastAPI(title=" Backend", version="1.0.0")


@app.on_event("startup")
def startup():
    create_tables()
    print("Database initialized successfully.")


@app.get("/")
def root():
    return {"status": "Running", "message": " Backend is running successfully!"}
