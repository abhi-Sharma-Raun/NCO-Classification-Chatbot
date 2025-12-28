from pydantic import BaseModel
from typing import Literal

class Session(BaseModel):
    session_id: str
    thread_id: str
    class config:
        from_attributes=True
    
class CreateNewChatResponse(BaseModel):
    thread_id: str
    
    
class Chat_input_schema(Session):
    user_message: str
    class Config:
        from_attributes=True
        

class ChatResponse(BaseModel):
    result: str
    status: Literal["MATCH_FOUND", "MORE_INFO"]
