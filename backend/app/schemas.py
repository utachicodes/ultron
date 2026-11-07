import json

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import UserRole


def _parse_json_field(value):
    if isinstance(value, str):
        return json.loads(value) if value else None
    return value


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.client


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class RegisterCreate(BaseModel):
    """Public self-registration. Role is never accepted from the client —
    new accounts are always created as `client`. Elevation happens only
    through the admin panel."""
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None


class PasswordChange(BaseModel):
    """Authenticated credential rotation. The current password is required so
    a stolen token cannot silently take over the account."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TemporaryPasswordOut(BaseModel):
    user_id: int
    email: str
    temporary_password: str


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ClientBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sector: Optional[str] = None
    is_active: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sector: Optional[str] = None
    is_active: Optional[bool] = None


class ClientOut(ClientBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScanScopeBase(BaseModel):
    target: str
    target_type: str
    is_excluded: bool = False
    verification_method: Optional[str] = None


class ScanScopeCreate(ScanScopeBase):
    pass


class ScanScopeUpdate(BaseModel):
    target: Optional[str] = None
    target_type: Optional[str] = None
    is_excluded: Optional[bool] = None
    verification_method: Optional[str] = None


class ScanScopeOut(ScanScopeBase):
    id: int
    client_id: int
    verified: bool
    verified_at: Optional[datetime] = None
    verification_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanBase(BaseModel):
    scan_type: str
    configuration: Optional[Dict[str, Any]] = None


class ScanCreate(ScanBase):
    client_id: int


class ScanClientOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class FindingBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    cvss_score: Optional[str] = None
    owasp_category: Optional[str] = None
    target: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    status: str = "open"


class FindingCreate(FindingBase):
    scan_id: int


class FindingReviewerOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class FindingAttachmentOut(BaseModel):
    id: int
    finding_id: int
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    uploaded_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FindingOut(FindingBase):
    id: int
    scan_id: int
    fingerprint: Optional[str] = None
    occurrence_count: int = 1
    first_seen_scan_id: Optional[int] = None
    reviewed_by_id: Optional[int] = None
    reviewed_by_user: Optional[FindingReviewerOut] = None
    reviewed_at: Optional[datetime] = None
    attachments: List[FindingAttachmentOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ScanOut(ScanBase):
    id: int
    client_id: int
    client: Optional[ScanClientOut] = None
    requested_by_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[Dict[str, Any]] = None
    findings: List[FindingOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("configuration", "summary", mode="before")
    @classmethod
    def _decode_json(cls, value):
        return _parse_json_field(value)


# --- Scan Schedules ---
class ScanScheduleBase(BaseModel):
    client_id: int
    scan_type: str = "vulnerability"
    interval_minutes: int = 1440


class ScanScheduleCreate(ScanScheduleBase):
    pass


class ScanScheduleUpdate(BaseModel):
    scan_type: Optional[str] = None
    interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ScanScheduleOut(ScanScheduleBase):
    id: int
    is_active: bool
    client: Optional[ScanClientOut] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str] = None
    client_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class APIKeyCreate(BaseModel):
    name: str


class APIKeyOut(BaseModel):
    id: int
    name: str
    owner_id: int
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyCreated(APIKeyOut):
    api_key: str


class AIQueryOut(BaseModel):
    id: int
    user_id: Optional[int]
    client_id: Optional[int]
    provider: str
    model: str
    prompt_sanitized: bool
    jailbreak_detected: bool = False
    jailbreak_category: Optional[str] = None
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Monitors (Continuous Monitoring) ---
class MonitorBase(BaseModel):
    target: str
    monitor_type: str
    client_id: int


class MonitorCreate(MonitorBase):
    pass


class MonitorUpdate(BaseModel):
    target: Optional[str] = None
    monitor_type: Optional[str] = None
    is_active: Optional[bool] = None
    baseline_config: Optional[str] = None


class MonitorOut(MonitorBase):
    id: int
    is_active: bool
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Alerts ---
class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    evidence: Optional[str] = None
    status: str = "open"


class AlertOut(AlertBase):
    id: int
    monitor_id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: str
    note: Optional[str] = None


# --- Code Scans ---
class CodeScanOut(BaseModel):
    id: int
    client_id: int
    repository_url: Optional[str]
    branch: Optional[str]
    status: str
    total_files: int
    issues_found: int
    created_at: datetime

    class Config:
        from_attributes = True


class CodeScanIssueOut(BaseModel):
    id: int
    code_scan_id: int
    file_path: Optional[str]
    line_number: Optional[int]
    issue_type: Optional[str]
    severity: Optional[str]
    description: Optional[str]
    remediation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Authz Hunts (autonomous IDOR/BOLA proof-of-exploit) ---
class AuthzRoleIn(BaseModel):
    """A named, authenticated identity to replay requests as (e.g. two
    different customer accounts, or a guest with no credentials)."""
    name: str
    headers: Dict[str, str] = {}


class AuthzProbeIn(BaseModel):
    """One request shape to replay across roles. `path` must contain a
    `{<id_param>}` placeholder, e.g. path="/api/invoices/{id}",
    id_param="id". `owner_value` is a real object id known to belong to
    `owner_role` (e.g. an invoice id for that logged-in customer)."""
    method: str = "GET"
    path: str
    id_param: str
    owner_role: str
    owner_value: str
    description: Optional[str] = None


class AuthzHuntCreate(BaseModel):
    client_id: int
    base_url: str
    roles: List[AuthzRoleIn]
    probes: List[AuthzProbeIn]


class BrowserLoginConfig(BaseModel):
    """A login form to drive before crawling, for apps with session-cookie
    auth rather than a bearer token."""
    url: str
    username_selector: str
    username: str
    password_selector: str
    password: str
    submit_selector: str


class BrowserCrawlRoleConfig(BaseModel):
    role_name: str
    start_url: str
    login: Optional[BrowserLoginConfig] = None


class BrowserCrawlRequest(BaseModel):
    base_url: str
    roles: List[BrowserCrawlRoleConfig]
    max_pages: int = 15


class AuthzFindingOut(BaseModel):
    id: int
    hunt_id: int
    method: str
    path: str
    owner_role: str
    tested_role: str
    verdict: str
    confidence: float
    severity: str
    reason: Optional[str] = None
    narrative: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("evidence", mode="before")
    @classmethod
    def _decode_evidence(cls, value):
        return _parse_json_field(value)


class AuthzHuntOut(BaseModel):
    id: int
    client_id: int
    base_url: str
    status: str
    probes_run: int
    confirmed_leaks: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[AuthzFindingOut] = []

    class Config:
        from_attributes = True


# --- PR Reviews (whitebox risk-ranked GitHub PR review) ---
class AIRedTeamResultOut(BaseModel):
    id: int
    run_id: int
    payload_id: Optional[str] = None
    category: Optional[str] = None
    verdict: str
    prompt_preview: Optional[str] = None
    response_preview: Optional[str] = None
    pattern_learned: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AIRedTeamExternalConfig(BaseModel):
    url: str
    headers: Dict[str, str] = {}
    prompt_field: str = "prompt"
    response_field: str = "response"


class AIRedTeamRunCreate(BaseModel):
    client_id: int
    mode: str = Field(default="internal", description="'internal' (Ultron's own AI Guard) or 'external'")
    external: Optional[AIRedTeamExternalConfig] = None
    force_local: bool = False


class AIRedTeamRunOut(BaseModel):
    id: int
    client_id: int
    mode: str
    target_summary: Optional[str] = None
    status: str
    payloads_run: int
    bypassed_count: int
    patterns_learned: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[AIRedTeamResultOut] = []

    class Config:
        from_attributes = True


class JailbreakPatternOut(BaseModel):
    id: int
    category: str
    pattern: str
    learned_from_run_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


