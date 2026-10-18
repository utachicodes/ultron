from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    client = "client"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.client)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    clients = relationship("Client", back_populates="owner")
    scans = relationship("Scan", back_populates="requested_by_user")
    findings = relationship("Finding", back_populates="reviewed_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("APIKey", back_populates="owner")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="clients")

    scopes = relationship("ScanScope", back_populates="client")
    scans = relationship("Scan", back_populates="client")


class ScanScope(Base):
    __tablename__ = "scan_scopes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    target = Column(String(500), nullable=False)
    target_type = Column(String(50), nullable=False)
    is_excluded = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    verification_method = Column(String(100))
    verification_token = Column(String(255))
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="scopes")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"))
    scan_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    configuration = Column(Text)
    summary = Column(Text)

    client = relationship("Client", back_populates="scans")
    requested_by_user = relationship("User", back_populates="scans")
    findings = relationship("Finding", back_populates="scan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False)
    cvss_score = Column(String(10))
    owasp_category = Column(String(100))
    target = Column(String(500))
    evidence = Column(Text)
    remediation = Column(Text)
    status = Column(String(50), default="open")
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="findings")
    reviewed_by_user = relationship("User", back_populates="findings")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_prefix = Column(String(12), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True))

    owner = relationship("User", back_populates="api_keys")


class AIQueryLog(Base):
    __tablename__ = "ai_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100))
    prompt_sanitized = Column(Boolean, default=False)
    prompt_hash = Column(String(255))
    response_hash = Column(String(255))
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
