from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func

from app.database.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
