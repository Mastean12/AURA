from sqlalchemy import Column, Integer, String, Text, DateTime, func, BigInteger

from app.database.database import Base


class AICache(Base):
    __tablename__ = "ai_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, nullable=False, index=True)
    doc_hash = Column(String(64), nullable=False, index=True)
    result_type = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
