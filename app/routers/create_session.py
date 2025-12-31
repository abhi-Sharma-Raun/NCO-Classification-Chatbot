from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from ..src import graph
from .. import models, schemas, utils
from ..database import get_db, engine


router = APIRouter(
    tags = ["Create New Session"]
)

@router.post("/create-new-session", status_code=status.HTTP_201_CREATED, response_model=schemas.Session)
def create_session(db: Session=Depends(get_db)):
    
    thread_id=uuid.uuid4()
    new_session=models.ChatSession(
        thread_id=thread_id,
        is_active=True
    )     
    try:
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is some backend problem.Please,Try after some time.Error: {e}")
   
    response={"session_id": str(new_session.session_id), "thread_id": str(new_session.thread_id)}
    
    return response