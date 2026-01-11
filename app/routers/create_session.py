from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from ..src import graph
from .. import models, schemas
from ..database import get_db


router = APIRouter(
    tags = ["Create and validate Session"]
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=schemas.USER_DATABASE_ERROR.model_dump())
   
    response={"session_id": str(new_session.session_id), "thread_id": str(new_session.thread_id)}
    
    return response


@router.post("/validate-SessionId-ThreadId", status_code=status.HTTP_200_OK)
def validate_session_id_thread_id(session_id: str, thread_id: str, db: Session=Depends(get_db)):
    session=db.query(models.ChatSession).filter(models.ChatSession.session_id==session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=schemas.INVALID_SESSION_ID_ERROR.model_dump())
    if not session.thread_id == thread_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.INVALID_THREAD_ID_ERROR.model_dump())
    return {"message": "VALID_SESSION"}  