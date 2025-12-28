from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from langgraph.types import Command
from . import utils
from .src import graph
from . import models, schemas
from .database import get_db, engine

models.Base.metadata.create_all(bind=engine)

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.post("/create-new-session", status_code=status.HTTP_201_CREATED, response_model=schemas.Session)
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is some backend problem.Please,Try after some time.Error: {e}")
   
    response={"session_id": str(new_session.session_id), "thread_id": str(new_session.thread_id)}
    
    return response


@app.post("/create-new-chat", status_code=status.HTTP_201_CREATED, response_model=schemas.CreateNewChatResponse)
def new_chat(session_id: str, db: Session = Depends(get_db)):
    
    session = (db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid.UUID(session_id)).with_for_update().one_or_none())

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please create new session")

    old_thread_id=str(session.thread_id)   
    is_active=session.is_active    
    utc_now=datetime.now(ZoneInfo("UTC"))
    session.thread_id=uuid.uuid4()
    session.is_active=True
    session.thread_created_at=utc_now
    session.thread_last_used_at=utc_now
    
    try:   
        db.commit()
        if is_active:
            utils.checkpointer.delete_thread(old_thread_id)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="There is some backend problem.Please,Try after some time")
    
    return {"thread_id": str(session.thread_id)}    
 
    
    
@app.put("/start", status_code=status.HTTP_200_OK, response_model=schemas.ChatResponse)
def start_chat(input_details: schemas.Chat_input_schema, db: Session=Depends(get_db)):
    
    session_id=input_details.session_id
    thread_id=input_details.thread_id
    user_msg=input_details.user_message
    
    read_session = (db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid.UUID(session_id)).with_for_update().one_or_none())
    if not read_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Session id.Please create a new session.")
    if str(read_session.thread_id)!=thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wrong thread_id.Please start a new chat.")
    if not read_session.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat is closed.Please start a new chat")
    
    read_session.thread_last_used_at=datetime.now(ZoneInfo("UTC"))
    db.commit()

    config={"configurable": {"thread_id": thread_id}}
    try:
        result=graph.graph.invoke(utils.generate_initial_state(user_msg), config=config)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"Please create a new chat and then try again. The error is {e}")     
        
    final_result=None  
    status = None 
    if "__interrupt__" in result:
        final_result=result['__interrupt__'][0].value
        status="MORE_INFO"
    else:   # when MATCH_FOUND        
        update_session=(db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid.UUID(session_id)).with_for_update().one_or_none())
        if update_session is None or not update_session.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat expired or closed. Please start a new chat.")
        final_result=result['messages'][-1].content
        status="MATCH_FOUND"
        
        update_session.is_active=False
        update_session.thread_closed_at=datetime.now(ZoneInfo("UTC"))
        db.commit()
        utils.checkpointer.delete_thread(thread_id) 
        
    return {"result": final_result, "status": status}
        


@app.put("/resume", status_code=status.HTTP_200_OK, response_model=schemas.ChatResponse)
def resume_chat(input_details: schemas.Chat_input_schema, db: Session=Depends(get_db)):
    session_id=input_details.session_id
    thread_id=input_details.thread_id
    user_message=input_details.user_message
    
    read_session = (db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid.UUID(session_id)).with_for_update().one_or_none())
    if not read_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Session id.Please create a new session.")
 
    if str(read_session.thread_id)!=thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wrong thread_id.Please start a new chat.")
    if not read_session.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat is closed.Please start a new chat")
   
    read_session.thread_last_used_at=datetime.now(ZoneInfo("UTC"))
    db.commit()

    config={"configurable": {"thread_id": thread_id}}
    try:
        result=graph.graph.invoke(Command(resume=user_message), config=config)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"Please create a new chat and then try again. The error is {e}")
    
    final_result=None
    status=None
    if "__interrupt__" in result:
        final_result=result['__interrupt__'][0].value
        status="MORE_INFO"
    else:                                                                     # for MATCH_Found
        update_session=(db.query(models.ChatSession).filter(models.ChatSession.session_id == uuid.UUID(session_id)).with_for_update().one_or_none())
        if update_session is None or not update_session.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat expired or closed. Please start a new chat.")
        final_result=result['messages'][-1].content
        status="MATCH_FOUND"
        
        update_session.is_active=False
        update_session.thread_closed_at=datetime.now(ZoneInfo("UTC"))
        db.commit()
        utils.checkpointer.delete_thread(thread_id) 
        
    return {"result": final_result, "status": status}