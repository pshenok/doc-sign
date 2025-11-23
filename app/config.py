from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration settings."""
    
    jwt_secret: str = "your-secret-key-change-this-in-production"
    database_path: str = "./data/documents.db"
    upload_dir: str = "./uploads"
    base_url: str = "http://localhost:8000"
    
    # JWT token expiration (in days)
    token_expiration_days: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Ensure required directories exist
def init_directories():
    """Create required directories if they don't exist."""
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
