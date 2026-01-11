from pydantic import BaseModel
from typing import Literal


class Session(BaseModel):
    
    '''Response validation schema when a new session is created'''
    
    session_id: str
    thread_id: str
    class config:
        from_attributes=True
    
    
class CreateNewChatResponse(BaseModel):
    
    '''Response validation schema when a new chat is created'''
    
    thread_id: str
    
    
class Chat_input_schema(CreateNewChatResponse):
    
    '''Input validation schema to validate the user's chat message input'''
    
    user_message: str
    class Config:
        from_attributes=True
        

class ChatResponse(BaseModel):
    
    '''Response validation schema for the reponse to user's chat message'''
    
    result: str
    status: Literal["MATCH_FOUND", "MORE_INFO"]


class ErrorDetail(BaseModel):
    detail: Literal["INVALID_SESSION_ID", "INVALID_THREAD_ID", "CLOSED_THREAD", "THREAD_ID_NOT_FOUND", "THREAD_ID_ALREADY_EXISTS", "DATABASE_ERROR", "MISSING_HEADER"]
    error_message: str
    class Config:
        from_attributes = True


# Session Related Errors
INVALID_SESSION_ID_ERROR=ErrorDetail(   
    detail = "INVALID_SESSION_ID", error_message = "Session ID does not exist.Please create a new session."
)
INVALID_THREAD_ID_ERROR=ErrorDetail(                                 #raised when thread_id does not exist in database
    detail = "INVALID_THREAD_ID", error_message = "Thread ID does not exist.Please create a new chat."
)

#Thread Related Errors
CLOSED_THREAD_ERROR=ErrorDetail(                                     #raised when trying to use a closed thread
    detail = "CLOSED_THREAD", error_message = "This chat is closed. Please start a new chat."
)
DELETE_THREAD_NOT_FOUND_ERROR=ErrorDetail(                           #raised when trying to delete a thread that does not exist in checkpoiter
    detail = "THREAD_ID_NOT_FOUND", error_message = "The thread to be deleted was not found in checkpoints.Create a new chat."
)
RESUME_THREAD_NOT_FOUND_ERROR=ErrorDetail(                           #raised when trying to resume a thread that does not exist in checkpointer
    detail = "THREAD_ID_NOT_FOUND", error_message = "The thread to be resumed was not found in checkpoints. Create a new chat."
)
START_THREAD_EXISTS_ERROR=ErrorDetail(                               #raised when trying to start a thread that already exists in checkpointer
    detail = "THREAD_ID_ALREADY_EXISTS", error_message = "The thread to be started already exists in checkpoints. Create a new chat."
)

# Internal Server Errors
USER_DATABASE_ERROR=ErrorDetail(
    detail = "DATABASE_ERROR", error_message = "There is some backend problem with user database. Please try after some time."
)
CHEDKPOINTER_DATABASE_ERROR=ErrorDetail(
    detail = "DATABASE_ERROR", error_message = "There is some backend problem with checkpointer database. Please try after some time."
)
DATABASE_ERROR=ErrorDetail(                                         #This is a generic database error
    detail = "DATABASE_ERROR", error_message = "There is some backend problem with database. Please try after some time."
)