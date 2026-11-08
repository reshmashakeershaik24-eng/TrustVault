from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "VIEWER"

class UserRegister(UserBase):
    password: str = Field(..., min_length=4)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Document Schemas
class DocumentOut(BaseModel):
    id: str
    owner_id: str
    title: str
    category: str
    file_name: str
    mime_type: str
    file_size: int
    file_hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailOut(DocumentOut):
    permissions: List["PermissionOut"] = []

# Permission Schemas
class PermissionGrant(BaseModel):
    user_email: EmailStr
    permission_level: str = "READ"  # READ, EDIT

class PermissionOut(BaseModel):
    id: str
    document_id: str
    user_id: str
    user_email: Optional[str] = None
    permission_level: str
    granted_by: str
    granted_at: datetime
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Audit Schemas
class AuditLogOut(BaseModel):
    id: str
    sequence_id: Optional[int] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    action: str
    status: str
    ip_address: Optional[str] = None
    details: Optional[str] = None
    previous_hash: str
    current_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class AuditVerificationResult(BaseModel):
    is_valid: bool
    total_records: int
    verified_records: int
    broken_sequence_id: Optional[int] = None
    message: str

# AI Suggestion Schemas
class AiSuggestionOut(BaseModel):
    id: str
    document_id: str
    suggested_user_id: str
    suggested_user_email: Optional[str] = None
    suggested_permission: str
    rationale: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AiSuggestionDecision(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")

