from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from .. import models, schemas, utils, auth
from ..database import get_db


router = APIRouter(
    tags = ["Create New Chat"]
)


@router.post("/create-new-chat", status_code=status.HTTP_201_CREATED, response_model=schemas.CreateNewChatResponse)
def new_chat(session_id: str = Depends(auth.get_session_id), db: Session = Depends(get_db)):
    
    uuid_session_id = utils.parse_uuid(session_id)
    if uuid_session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id")
    
    session = (db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid_session_id).with_for_update().one_or_none())

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please create new session")

    old_thread_id=str(session.thread_id)   
    was_active=session.is_active    
    utc_now=datetime.now(ZoneInfo("UTC"))
    session.thread_id=uuid.uuid4()
    session.is_active=True
    session.thread_created_at=utc_now
    session.thread_last_used_at=utc_now
    
    try:   
        db.commit()
        checkpoints = list(utils.checkpointer.list({"configurable": {"thread_id": old_thread_id}}))
        if len(checkpoints)>0 and was_active:          # If the old thread exists in checkpoints and was active then that old thread should be deleted
            print("Thread exists.")                    #If the thread exists and the session is not active then that thread will be automatically deleted from checkpoints by triggers
            utils.checkpointer.delete_thread(old_thread_id)
    except:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="There is some backend problem.Please,Try after some time")
    
    return {"thread_id": str(session.thread_id)}    