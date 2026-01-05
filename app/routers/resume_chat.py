from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from langgraph.types import Command
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from ..src import graph
from .. import models, schemas, utils, auth
from ..database import get_db


router=APIRouter(
    tags=["Resume the chat"]
)


@router.put("/resume", status_code=status.HTTP_200_OK, response_model=schemas.ChatResponse)
def resume_chat(input_details: schemas.Chat_input_schema, db: Session=Depends(get_db), session_id: str = Depends(auth.get_session_id)):
    session_id=session_id
    thread_id=input_details.thread_id
    user_message=input_details.user_message
    
    uuid_session_id = utils.parse_uuid(session_id)
    uuid_thread_id = utils.parse_uuid(thread_id)
    if uuid_session_id is None or uuid_thread_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id or thread_id")
    
    read_session = (db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid_session_id).with_for_update().one_or_none())
    if not read_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Session id.Please create a new session.")
 
    if read_session.thread_id!=uuid_thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wrong thread_id.Please start a new chat.")
    if not read_session.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat is closed.Please start a new chat")
   
    read_session.thread_last_used_at=datetime.now(ZoneInfo("UTC"))
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="There is some problem with backend")


    config={"configurable": {"thread_id": thread_id}}
    try:
        checkpoints = utils.checkpointer.get_tuple(config)
        if checkpoints is None:                  # If the thread doesn't exist in checkpoints means it hasn't been used before so that thread can't be used for resume in graph
#            print("Thread does not exist.Can't be used for resume")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This thread can't be used to resume the chat.Create a new chat then try again")
    
        result=graph.graph.invoke(Command(resume=user_message), config=config, durability="exit")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Please create a new chat and then try again.")
    
    final_result=None
    curr_status=None
    if "__interrupt__" in result:
        final_result=result['__interrupt__'][0].value
        curr_status="MORE_INFO"
    else:                                                                     # for MATCH_Found
        update_session=(db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid_session_id).with_for_update().one_or_none())
        if update_session is None or not update_session.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat expired or closed. Please start a new chat.")
        final_result=result['messages'][-1].content
        curr_status="MATCH_FOUND"
        
        update_session.is_active=False
        update_session.thread_closed_at=datetime.now(ZoneInfo("UTC"))
        try:
            db.commit()
            checkpoints = utils.checkpointer.get_tuple(config)
            if checkpoints is not None:    # If the thread exists then only delete it
                utils.checkpointer.delete_thread(thread_id) 
        except:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="backend database problem with checkpointer or database commit")
        
    return {"result": final_result, "status": curr_status}