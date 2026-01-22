from .database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import text
import uuid
from datetime import datetime

class ChatSession(Base):   
    __tablename__="chatsession"
    session_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    thread_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(server_default=text("false"), nullable=False)   # This is the sorce of truth if a thread/chat is active and can be resumed or not
    session_created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    thread_created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    thread_closed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    thread_last_used_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)   # It is only treated as a heartbeat not proof of success
    
