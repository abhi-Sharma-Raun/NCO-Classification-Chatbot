from fastapi import Header, HTTPException, status
from . import utils, schemas

MISSING_HEADER_ERROR = schemas.ErrorDetail(detail="MISSING_HEADER", error_message="Session-Id header missing")

def get_session_id(session_id: str | None = Header(default=None)):
    
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_HEADER_ERROR.model_dump())
    
    uuid_session_id = utils.parse_uuid(session_id)
    if uuid_session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=schemas.INVALID_SESSION_ID_ERROR.model_dump())
        
    return session_id
