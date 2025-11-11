from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.config import settings
from app.routes import auth, admin, teacher

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Exam Paper Generator with Multi-Agent AI",
    version="1.0.0"
)

# CORS middleware configuration
origins = [
    "http://localhost:5173",    # Vite dev server
    "http://localhost:3000",    # Alternative local development
    "http://127.0.0.1:5173",   # Alternative local address
    "http://127.0.0.1:3000",   # Alternative local address
    "https://exam-paper-generator-frontend.onrender.com",  # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await connect_to_mongo()
    print(f"🚀 {settings.APP_NAME} started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()

# Health check
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Intelligent Exam Paper Generator API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational"
    }

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(teacher.router)

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))  # Render sets PORT dynamically
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
