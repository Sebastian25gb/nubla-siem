from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    policy_id = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tenants = relationship("UserTenantRole", back_populates="user", cascade="all, delete-orphan")

class UserTenantRole(Base):
    __tablename__ = "user_tenant_roles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String, nullable=False)
    __table_args__ = (
        CheckConstraint("role in ('admin','analyst','viewer')", name="ck_role"),
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )
    user = relationship("User", back_populates="tenants")
    tenant = relationship("Tenant")