from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func

from app.database.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    theme_color = Column(String(7), default="#2563eb")
    description = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    subscription_plan = Column(String(20), default="free")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationSecurity(Base):
    __tablename__ = "org_security"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    password_min_length = Column(Integer, default=8)
    password_require_special = Column(Boolean, default=True)
    password_expiry_days = Column(Integer, default=90)
    session_timeout_minutes = Column(Integer, default=60)
    require_mfa = Column(Boolean, default=False)
    require_email_verification = Column(Boolean, default=True)
    allow_public_invitations = Column(Boolean, default=True)
    lock_inactive_days = Column(Integer, default=180)
    force_password_reset = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationAIConfig(Base):
    __tablename__ = "org_ai_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    ai_provider = Column(String(20), default="gemini")
    executive_intelligence = Column(Boolean, default=True)
    risk_analysis = Column(Boolean, default=True)
    forecasting = Column(Boolean, default=True)
    recommendations = Column(Boolean, default=True)
    board_reports = Column(Boolean, default=True)
    document_chat = Column(Boolean, default=True)
    knowledge_search = Column(Boolean, default=True)
    monthly_budget_cents = Column(Integer, default=5000)
    max_daily_requests = Column(Integer, default=1000)
    max_monthly_requests = Column(Integer, default=30000)
    auto_shutdown_threshold = Column(Integer, default=80)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationDataGovernance(Base):
    __tablename__ = "org_data_governance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    data_retention_days = Column(Integer, default=365)
    max_upload_size_mb = Column(Integer, default=50)
    allowed_file_types = Column(Text, default="pdf,docx,xlsx,csv,txt")
    document_retention_days = Column(Integer, default=365)
    gdpr_compliant = Column(Boolean, default=False)
    soc2_compliant = Column(Boolean, default=False)
    iso27001_compliant = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
