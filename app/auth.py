from fastapi import Header, HTTPException, status
from . import utils

def get_session_id(session_id: str | None = Header(default=None)):
    
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session-Id header missing")
    
    uuid_session_id = utils.parse_uuid(session_id)
    if uuid_session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
        
    return session_id
