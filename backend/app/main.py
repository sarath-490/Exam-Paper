from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.config import settings
from app.routes import auth, admin, teacher
import os
import uvicorn

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Exam Paper Generator with Multi-Agent AI",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://exam-paper.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    print(f"🚀 {settings.APP_NAME} started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Intelligent Exam Paper Generator API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "api": "operational"}

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(teacher.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)
