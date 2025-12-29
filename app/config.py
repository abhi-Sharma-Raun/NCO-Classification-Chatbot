from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_username: str
    database_password: str
    database_hostname: str
    database_port: int
    database_name: str
    checkpointer_database_name: str
    groq_api_key: str
    langsmith_tracing: bool
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str
    
    class Config:
        env_file = ".env"
    
settings=Settings()