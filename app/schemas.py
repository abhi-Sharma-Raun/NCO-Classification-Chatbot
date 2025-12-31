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
