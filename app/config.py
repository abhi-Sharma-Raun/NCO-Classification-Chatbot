from pydantic_settings import BaseSettings
import os
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    checkpointer_db_password: str
    checkpointer_db_host: str
    checkpointer_db_username: str
    checkpointer_db_dbname: str
    database_password: str
    database_region: str
    database_host: str
    database_username: str
    groq_api_key: str
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    allowed_url1: str
    allowed_url2: str
    allowed_url3: str
    
    class Config:
        env_file = ".env"
    
settings=Settings()


BASE_DIR = Path(__file__).resolve().parents[1]
EMBEDDINGS_PATH = Path(BASE_DIR / "embeddings") 


