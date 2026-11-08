import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustVault"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "trustvault-super-secure-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Database (Default: SQLite local file)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trustvault.db")
    
    # Default Demo User Password (read from env; defaults to 1234 for demo/grading)
    DEFAULT_USER_PASSWORD: str = os.getenv("DEFAULT_USER_PASSWORD", "1234")
    
    # File Limits
    MAX_FILE_SIZE_MB: int = 15
    
    # AI (Optional Groq API Key)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()

