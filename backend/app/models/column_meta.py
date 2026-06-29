from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, func
from app.database.database import Base


class ColumnMetadata(Base):
    __tablename__ = "column_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)
    dtype = Column(String(50), nullable=True)
    nunique = Column(Integer, nullable=True)
    cardinality = Column(String(20), nullable=True)
    missing = Column(Integer, nullable=True)
    missing_pct = Column(Float, nullable=True)
    min_val = Column(Float, nullable=True)
    max_val = Column(Float, nullable=True)
    mean_val = Column(Float, nullable=True)
    std_val = Column(Float, nullable=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    has_duplicates = Column(Boolean, default=False)
    is_skewed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
