from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func

from app.database.database import Base


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_type = Column(String(50), nullable=False)
    provider = Column(String(20), nullable=True)
    model = Column(String(50), nullable=True)
    tokens_estimated = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
