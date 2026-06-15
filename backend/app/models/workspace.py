from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.database.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    workspace_type = Column(String(50), default="department")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="active")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="analyst")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True)
    ai_provider = Column(String(20), default="gemini")
    executive_insights = Column(Integer, default=1)
    forecasting = Column(Integer, default=1)
    risk_analysis = Column(Integer, default=1)
    recommendations = Column(Integer, default=1)
    allow_uploads = Column(Integer, default=1)
    allow_ai_chat = Column(Integer, default=1)
    allow_analytics = Column(Integer, default=1)
    allow_pdf_export = Column(Integer, default=1)
    allow_executive_reports = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
