from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

#SQL_DATABASE_URL=f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

NEON_DATABASE_URL = 'postgresql://neondb_owner:npg_6AaO7sZbVTvi@ep-weathered-bonus-a4csd9vd-pooler.us-east-1.aws.neon.tech/nco-classification-chatbot?sslmode=require&channel_binding=require'

engine = create_engine(
    NEON_DATABASE_URL,
    pool_size=1,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()