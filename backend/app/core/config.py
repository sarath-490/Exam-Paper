from pydantic_settings import BaseSettings
from typing import ClassVar, Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ===== Gemini AI =====
    GEMINI_API_KEY: str

    # ===== MongoDB Atlas =====
    MONGODB_URI: str  # MongoDB Atlas connection string
    MONGODB_DB_NAME: str = "exam_paper_ai"

    # Legacy support (will use MONGODB_URI)
    @property
    def MONGO_URI(self) -> str:
        return self.MONGODB_URI

    # ===== Cloudinary =====
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # ===== JWT =====
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Alias for SECRET_KEY (for compatibility)
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET

    # ===== Application =====
    APP_NAME: str = "Intelligent Exam Paper Generator"

    # Use ClassVar since these are static constants, not environment settings
    BACKEND_URL: ClassVar[str] = "https://exam-paper-backend.onrender.com"
    FRONTEND_URL: ClassVar[str] = "https://exam-paper-backend.onrender.com"
    FRONTEND_ALLOWED_ORIGINS: ClassVar[str] = "https://exam-paper.onrender.com"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return self.FRONTEND_ALLOWED_ORIGINS.split(",")

    # ===== File Upload =====
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
        "image/jpeg",
        "image/png",
        "image/jpg",
        "image/webp",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env for backward compatibility


settings = Settings()
