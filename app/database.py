from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from .config import settings
from psycopg import connect
from langgraph.checkpoint.postgres import PostgresSaver


# I am using neon for User-database and Supabase for checkpointer-database

'''
Setting up the User-database connection using SQLAlchemy.It is a Pooling connection.Neon is not being used for checkpoints as it is not persistent and
langgraph uses psycopg Connection objects which don't implement how to handle non-persistent connections 
'''
DATABASE_URL_USER = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_host}.{settings.database_region}.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
engine = create_engine(
    DATABASE_URL_USER,
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
         
         
'''
Setting up checkpointer-database connection from supabase using psycopg.It is a session Pooler and persistent connection which is good for langgraph checkpointer.
'''    

#Setting up checkpointer database though it is one time process so one can remove this if the database is set.     
with connect(user=f'{settings.checkpointer_db_username}', password=f'{settings.checkpointer_db_password}', host=f'{settings.checkpointer_db_host}', port=5432, dbname=f'{settings.checkpointer_db_dbname}',autocommit=True) as conn:
    saver = PostgresSaver(conn)
    saver.setup()
# Setting up Pool Connection for Checkpointer
DATABASE_URL_CHECKPOINTS = f'postgresql://{settings.checkpointer_db_username}:{settings.checkpointer_db_password}@{settings.checkpointer_db_host}:5432/{settings.checkpointer_db_dbname}'
checkpointer_pool=ConnectionPool(
    conninfo=DATABASE_URL_CHECKPOINTS,
    min_size=2,
    max_size=3,   
    kwargs={
        "row_factory": dict_row
    }
)