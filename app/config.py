from pydantic_settings import BaseSettings

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
    
    class Config:
        env_file = ".env"
    
settings=Settings()