from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func

from app.database.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
