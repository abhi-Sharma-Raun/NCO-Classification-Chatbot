from fastapi import Header, HTTPException
from . import utils

def get_session_id(session_id: str | None = Header(default=None)):
    if session_id is None:
        raise HTTPException(
            status_code=400,
            detail="Session-Id header missing"
        )
    return session_id
