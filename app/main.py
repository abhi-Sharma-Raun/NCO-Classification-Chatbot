from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine, checkpointer_pool
from .routers import create_session, create_chat, start_chat, resume_chat
from .config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from contextlib import asynccontextmanager


async def create_table_if_not_exists():
    async with engine.connect() as conn:
        print("connected to the user database")
        await conn.run_sync(models.Base.metadata.create_all)
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("trying to create tables if not exists")
    await create_table_if_not_exists()
    await checkpointer_pool.open()
    async with checkpointer_pool.connection() as conn:
        # We create a temporary saver just for the setup() call
        temp_saver = AsyncPostgresSaver(conn)
        await temp_saver.setup()
    yield
    
    await checkpointer_pool.close()
    

app=FastAPI(lifespan=lifespan)

app.include_router(create_session.router)
app.include_router(create_chat.router)
app.include_router(start_chat.router)
app.include_router(resume_chat.router)
        
@app.get("/")
def read_root():    # This is just the route which is used to wake up the API on platforms like render free teir
    return {"message": "Welcome to the NCO Classification Chatbot API"}
             
app.add_middleware(
    CORSMiddleware,
    allow_origins = [f"{settings.allowed_url1}", f"{settings.allowed_url2}", f"{settings.allowed_url3}"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)
