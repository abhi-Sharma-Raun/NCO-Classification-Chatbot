from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


NEON_DATABASE_URL = f'postgresql://neondb_owner:{settings.database_password}@ep-rough-darkness-adak90jk-pooler.c-2.{settings.database_region}.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

engine = create_engine(
    NEON_DATABASE_URL,
    pool_size=2,
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