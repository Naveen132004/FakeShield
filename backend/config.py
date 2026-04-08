"""
config.py
=========
Backend configuration and environment settings.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Fake News Detector API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # ML Model paths (relative to backend directory)
    MODEL_PATH: str = "../ml/models/fake_news_model.joblib"
    PREPROCESSOR_PATH: str = "../ml/models/preprocessor.joblib"
    
    # MongoDB (optional - for history storage)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "fake_news_detector"
    
    # News API (optional)
    NEWS_API_KEY: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
