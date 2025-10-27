from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://avnadmin:AVNS_h6y0Do7ecnCZLW2jvdC@pg-38d9e6ab-tech-1984.i.aivencloud.com:19934/defaultdb?sslmode=require"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:4000", "http://127.0.0.1:4000", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500", "http://127.0.0.1:5500"]
    
    # SMS Vendor Settings
    SMS_VENDOR_URL: str = "https://api.smsvendor.com"
    SMS_VENDOR_API_KEY: str = "your-sms-vendor-api-key"
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379"
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"

settings = Settings()
