from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    
    # Database
    DB_PATH: str = "storyteller.db"
    
    # Audio & Visual APIs
    KOKORO_TTS_URL: str = "http://192.168.0.14:8880/dev/captioned_speech"
    COMFYUI_API_URL: str = "http://192.168.0.14:8188"
    
    # App Config
    APP_NAME: str = "Storyteller v2.0"
    DEBUG_MODE: bool = True
    
    # NocoDB Field Mapping - DEPRECATED / REMOVED
    # Kept empty dict to prevent import errors if referenced elsewhere
    NOCODB_FIELDS: dict = {
        "project": {},
        "chapter": {}
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
