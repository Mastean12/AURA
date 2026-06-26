from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func
from app.database.database import Base


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, nullable=False, unique=True, index=True)
    data_quality_score = Column(Float, nullable=True)
    data_quality_grade = Column(String(20), nullable=True)
    statistical_confidence = Column(Float, nullable=True)
    issues_count = Column(Integer, default=0)
    issues_json = Column(Text, nullable=True)
    suggestions_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
