from sqlalchemy import Column, Integer, String, DateTime, func, BigInteger

from app.database.database import Base


class EmbeddingMetadata(Base):
    __tablename__ = "embeddings_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, nullable=False, index=True)
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
