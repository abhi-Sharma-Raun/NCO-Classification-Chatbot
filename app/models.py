from .database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP, Boolean
from sqlalchemy import Column
from sqlalchemy.sql.expression import text

class ChatSession(Base):   
    __tablename__="chatsession"
    session_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    thread_id = Column(UUID(as_uuid=True), nullable=False)
    is_active = Column(Boolean, server_default=text("false"), nullable=False)   # This is the sorce of truth if a thread/chat is active and can be resumed or not
    session_created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    thread_created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    thread_closed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    thread_last_used_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)   # It is only treated as a heartbeat not proof of success
    
