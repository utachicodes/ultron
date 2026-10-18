import json

from pydantic import BaseModel, field_validator
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
    password: str


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
    is_active: bool = True


class ClientCreate(ClientBase):
    pass


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


class FindingOut(FindingBase):
    id: int
    scan_id: int
    reviewed_by_id: Optional[int] = None
    reviewed_by_user: Optional[FindingReviewerOut] = None
    reviewed_at: Optional[datetime] = None
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
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
