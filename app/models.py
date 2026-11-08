import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, LargeBinary, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="VIEWER")  # ADMIN, OWNER, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    owned_documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    permissions = relationship("DocumentPermission", foreign_keys="DocumentPermission.user_id", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, default="GENERAL", index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)  # Stored private inside database
    file_hash = Column(String(64), nullable=False)   # SHA-256
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    owner = relationship("User", back_populates="owned_documents")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    ai_suggestions = relationship("AiSuggestion", back_populates="document", cascade="all, delete-orphan")

class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    permission_level = Column(String(50), nullable=False, default="READ")  # READ, EDIT
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=utc_now)
    revoked_at = Column(DateTime, nullable=True)  # Set immediately on revocation

    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="permissions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sequence_id = Column(Integer, primary_key=False, autoincrement=True, unique=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    document_id = Column(String(36), nullable=True, index=True)
    document_title = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)  # UPLOAD, DOWNLOAD, READ, EDIT, DELETE, GRANT, REVOKE, DENIED_ACCESS, LOGIN
    status = Column(String(20), nullable=False)  # ALLOWED, DENIED
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, index=True)

class AiSuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    suggested_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    suggested_permission = Column(String(50), nullable=False, default="READ")
    rationale = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED
    decided_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    decided_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="ai_suggestions")
    suggested_user = relationship("User", foreign_keys=[suggested_user_id])

