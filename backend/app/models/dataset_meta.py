from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.database.database import Base


class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, nullable=False, unique=True, index=True)
    industry = Column(String(100), nullable=True)
    dataset_type = Column(String(100), nullable=True)
    target_variable = Column(String(255), nullable=True)
    time_column = Column(String(255), nullable=True)
    kpis = Column(Text, nullable=True)
    identifier_columns = Column(Text, nullable=True)
    overridden = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
