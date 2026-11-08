from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Document, DocumentPermission
from app.security import get_current_user
from app.audit import log_audit_event

def verify_document_access(
    document_id: str,
    required_level: str,
    current_user: User,
    db: Session,
    request: Optional[Request] = None
) -> Document:
    # 1. Fetch document
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        # Prevent IDOR discovery: return 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # 2. Check Document Owner (Full Access)
    if doc.owner_id == current_user.id:
        return doc

    # 3. Check Granular Active Permissions
    perm = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == current_user.id,
        DocumentPermission.revoked_at == None  # Immediate revocation invariant
    ).first()

    if perm:
        if required_level == "READ" and perm.permission_level in ["READ", "EDIT"]:
            return doc
        if required_level == "EDIT" and perm.permission_level == "EDIT":
            return doc

    # 4. Access Refused -> Strict Server Invariant: Must log refusal to Audit Trail
    log_audit_event(
        db=db,
        action="DENIED_ACCESS",
        status="DENIED",
        user_id=current_user.id,
        user_email=current_user.email,
        document_id=doc.id,
        document_title=doc.title,
        details=f"Unauthorized attempt to {required_level} document without valid grant",
        request=request
    )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access Denied: You do not have permission to access this document"
    )

# FastAPI Dependencies for Endpoints
def verify_document_read_access(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> Document:
    # THE AUTHORIZATION LINE (Interview Core Checkpoint)
    return verify_document_access(document_id, "READ", current_user, db, request)

def verify_document_edit_access(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> Document:
    return verify_document_access(document_id, "EDIT", current_user, db, request)

