from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings and configuration
    Load from environment variables or .env file
    """
    # Application Settings
    APP_NAME: str = "Pebble Outreach"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    DEBUG: bool = True
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    PROJECT_ROOT: str = "/home/vedanschi/pebble-outreach"
    
    # Database Settings
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False
    
    # Security Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    MIN_PASSWORD_LENGTH: int = 8
    
    # Together AI Settings
    TOGETHER_API_KEY: str
    TOGETHER_MODEL_NAME: str = "google/gemma-2-27b-it"
    TOGETHER_API_URL: str = "https://api.together.ai/inference"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    
    # Email Settings
    DEFAULT_SMTP_HOST: str = "smtp.gmail.com"
    DEFAULT_SMTP_PORT: int = 587
    DEFAULT_SMTP_USE_TLS: bool = True
    EMAIL_TEMPLATE_DIR: str = "templates/email"
    EMAIL_RATE_LIMIT: int = 50  # emails per minute
    EMAIL_BATCH_SIZE: int = 20
    EMAIL_RETRY_ATTEMPTS: int = 3
    
    # Storage Settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5_242_880  # 5MB in bytes
    ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "xls"]
    
    # Cache Settings
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # Monitoring Settings
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Optional Cloud Storage (Cloudflare R2)
    R2_ENABLED: bool = False
    R2_BUCKET_NAME: Optional[str] = None
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_ENDPOINT_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def database_settings(self) -> Dict[str, Any]:
        """Get all database-related settings"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "echo": self.DB_ECHO
        }

    @property
    def email_settings(self) -> Dict[str, Any]:
        """Get default email settings"""
        return {
            "host": self.DEFAULT_SMTP_HOST,
            "port": self.DEFAULT_SMTP_PORT,
            "use_tls": self.DEFAULT_SMTP_USE_TLS,
            "rate_limit": self.EMAIL_RATE_LIMIT,
            "batch_size": self.EMAIL_BATCH_SIZE,
            "retry_attempts": self.EMAIL_RETRY_ATTEMPTS
        }

    @property
    def llm_settings(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            "api_key": self.TOGETHER_API_KEY,
            "model": self.TOGETHER_MODEL_NAME,
            "api_url": self.TOGETHER_API_URL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "top_p": self.TOP_P
        }

@lru_cache()
def get_settings() -> Settings:
    """
    Create cached instance of settings.
    This will prevent multiple reads from env files
    """
    return Settings()

# Create settings instance
settings = get_settings()