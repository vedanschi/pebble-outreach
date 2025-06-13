from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Pebble Outreach"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    
    # Database Settings
    DATABASE_URL: str

    # JWT Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI Settings
    OPENAI_API_KEY: str

    # SMTP Settings
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_SENDER_EMAIL: str
    SMTP_USE_TLS: bool = True

    class Config:
        env_file = ".env"

settings = Settings()