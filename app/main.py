from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import create_session, create_chat, start_chat, resume_chat
from .config import settings


models.Base.metadata.create_all(bind=engine)

app=FastAPI()

app.include_router(create_session.router)
app.include_router(create_chat.router)
app.include_router(start_chat.router)
app.include_router(resume_chat.router)
        
             
app.add_middleware(
    CORSMiddleware,
    allow_origins = [f"{settings.allowed_url1}", f"{settings.allowed_url2}"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)
