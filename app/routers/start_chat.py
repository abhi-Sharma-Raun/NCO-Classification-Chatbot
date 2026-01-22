from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from zoneinfo import ZoneInfo
from ..src import graph
from .. import models, schemas, utils, auth
from ..database import get_db
import time


router=APIRouter(
    tags=["Start the chat"]
)


@router.put("/start", status_code=status.HTTP_200_OK, response_model=schemas.ChatResponse)
async def start_chat(input_details: schemas.Chat_input_schema, db: AsyncSession=Depends(get_db), session_id: str = Depends(auth.get_session_id)):
    
    session_id=session_id
    thread_id=input_details.thread_id
    user_msg=input_details.user_message
    
    time_started=time.time()
    uuid_session_id = utils.parse_uuid(session_id)
    uuid_thread_id = utils.parse_uuid(thread_id)
    
    if uuid_session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.INVALID_SESSION_ID_ERROR.model_dump())
    if uuid_thread_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.INVALID_THREAD_ID_ERROR.model_dump())
    
    stmt_read = select(models.ChatSession).where(models.ChatSession.session_id == uuid_session_id)
    read_session = (await db.execute(stmt_read)).scalar_one_or_none()
    if not read_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.INVALID_SESSION_ID_ERROR.model_dump())
    if read_session.thread_id!=uuid_thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=schemas.INVALID_THREAD_ID_ERROR.model_dump())
    if not read_session.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=schemas.CLOSED_THREAD_ERROR.model_dump())
    
    read_session.thread_last_used_at=datetime.now(ZoneInfo("UTC"))
    try:
        await db.commit()
        time_ended=time.time()
        print(f"Time taken to read and update session: {time_ended - time_started} seconds")
    except:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=schemas.DATABASE_ERROR.model_dump())
    

    config={"configurable": {"thread_id": thread_id}}
    
    try:
        checkpoints = await utils.checkpointer.aget_tuple(config)
        if checkpoints is not None:                  # If the thread already exists in checkpoints means it has been used before so that thread can't be used for start invoke in graph
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=schemas.START_THREAD_EXISTS_ERROR.model_dump())

        result=await graph.graph.ainvoke(utils.generate_initial_state(user_msg), config=config, durability="exit")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception in starting chat: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=schemas.CHEDKPOINTER_DATABASE_ERROR.model_dump())     
        
    final_result=None  
    curr_status = None 
    if "__interrupt__" in result:
        final_result=result['__interrupt__'][0].value
        curr_status="MORE_INFO"
    else:   # when MATCH_FOUND       
        stmt_update = select(models.ChatSession).where(models.ChatSession.session_id == uuid_session_id).with_for_update()
        result_update = await db.execute(stmt_update)
        update_session = result_update.scalar_one_or_none()
        
        if update_session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=schemas.INVALID_SESSION_ID_ERROR.model_dump())
        if not update_session.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.CLOSED_THREAD_ERROR.model_dump())

        final_result=result['messages'][-1].content
        curr_status="MATCH_FOUND"
        
        update_session.is_active=False
        update_session.thread_closed_at=datetime.now(ZoneInfo("UTC"))
        try:
            await db.commit()
            checkpoints = await utils.checkpointer.aget_tuple(config)
            if checkpoints is not None:    # If the thread exists then only delete it
                await utils.checkpointer.adelete_thread(thread_id) 
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=schemas.DATABASE_ERROR.model_dump())
        
    return {"result": final_result, "status": curr_status}