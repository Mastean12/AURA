from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func, BigInteger

from app.database.database import Base


PLANS = {
    "free": {"name": "Starter", "price_cents": 0, "users": 3, "workspaces": 1, "documents": 100, "ai_requests": 500, "storage_mb": 5120},
    "starter": {"name": "Starter", "price_cents": 2900, "users": 3, "workspaces": 1, "documents": 100, "ai_requests": 500, "storage_mb": 5120},
    "professional": {"name": "Professional", "price_cents": 9900, "users": 15, "workspaces": 5, "documents": 1000, "ai_requests": 5000, "storage_mb": 51200},
    "business": {"name": "Business", "price_cents": 29900, "users": 50, "workspaces": 999, "documents": 10000, "ai_requests": 25000, "storage_mb": 256000},
    "enterprise": {"name": "Enterprise", "price_cents": 0, "users": 99999, "workspaces": 99999, "documents": 999999, "ai_requests": 999999, "storage_mb": 999999},
}


class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan = Column(String(20), default="free")
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_company = Column(String(255), nullable=True)
    tax_vat = Column(String(50), nullable=True)
    billing_address = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    currency = Column(String(3), default="USD")
    po_number = Column(String(50), nullable=True)
    subscription_status = Column(String(20), default="active")
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="pending")
    plan_name = Column(String(50), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
