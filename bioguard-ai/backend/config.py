"""Configuration settings loaded from environment variables."""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings."""
    
    sensor_mode: Literal["mock", "pi"] = "mock"
    mock_update_interval: int = 5
    port: int = 8000
    cors_origin: str = "http://localhost:3000"
    database_url: str = "sqlite:///./bioguard.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
