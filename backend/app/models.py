from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum, Float
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
    # Drives compliance/report sector-specific obligations (reports.py,
    # compliance.py already read this via getattr(client, "sector", None)).
    sector = Column(String(50))
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
    findings = relationship("Finding", back_populates="scan", foreign_keys="Finding.scan_id")


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
    fingerprint = Column(String(64), index=True)
    first_seen_scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    occurrence_count = Column(Integer, default=1)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="findings", foreign_keys=[scan_id])
    reviewed_by_user = relationship("User", back_populates="findings")
    attachments = relationship("FindingAttachment", back_populates="finding", cascade="all, delete-orphan")


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


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    target = Column(String(500), nullable=False)
    monitor_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    baseline_config = Column(Text)  # JSON
    last_check = Column(DateTime(timezone=True))
    next_check = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="monitors")
    alerts = relationship("Alert", back_populates="monitor")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False)
    evidence = Column(Text)  # JSON
    status = Column(String(50), default="open")  # open, acknowledged, resolved, false_positive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    monitor = relationship("Monitor", back_populates="alerts")


class ScanSchedule(Base):
    __tablename__ = "scan_schedules"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    scan_type = Column(String(50), default="vulnerability", nullable=False)
    interval_minutes = Column(Integer, default=1440, nullable=False)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class CodeScan(Base):
    __tablename__ = "code_scans"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    repository_url = Column(String(500))
    branch = Column(String(100))
    status = Column(String(50), default="pending")
    total_files = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class FindingAttachment(Base):
    __tablename__ = "finding_attachments"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    finding = relationship("Finding", back_populates="attachments")
    uploaded_by = relationship("User")


class CodeScanIssue(Base):
    __tablename__ = "code_scan_issues"

    id = Column(Integer, primary_key=True, index=True)
    code_scan_id = Column(Integer, ForeignKey("code_scans.id"), nullable=False)
    file_path = Column(String(500))
    line_number = Column(Integer)
    issue_type = Column(String(100))  # hardcoded_secret, insecure_default, vulnerable_dep, logic_flaw
    severity = Column(String(20))
    description = Column(Text)
    remediation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Add relationships to Client
Client.monitors = relationship("Monitor", back_populates="client")
