from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Document, DocumentPermission, generate_uuid, utc_now
from app.schemas import PermissionGrant, PermissionOut
from app.security import get_current_user
from app.audit import log_audit_event

router = APIRouter(prefix="/documents/{document_id}/permissions", tags=["Permissions"])

@router.post("", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def grant_permission(
    document_id: str,
    grant_in: PermissionGrant,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch document
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Authorization: Only document owner can grant permissions
    if doc.owner_id != current_user.id:
        log_audit_event(
            db=db,
            action="DENIED_ACCESS",
            status="DENIED",
            user_id=current_user.id,
            user_email=current_user.email,
            document_id=doc.id,
            document_title=doc.title,
            details=f"Unauthorized attempt to grant document permissions by {current_user.role} {current_user.email}",
            request=request
        )
        raise HTTPException(status_code=403, detail="Only the document owner can grant permissions")

    # 3. Find target user
    target_email = grant_in.user_email.lower().strip()
    target_user = db.query(User).filter(User.email == target_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User with email '{target_email}' does not exist")

    if target_user.id == doc.owner_id:
        raise HTTPException(status_code=400, detail="Cannot grant permission to the document owner (already has full access)")

    # 4. Check for existing active or revoked permission
    existing_perm = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == target_user.id
    ).first()

    level = grant_in.permission_level.upper()
    if level not in ["READ", "EDIT"]:
        level = "READ"

    if existing_perm:
        existing_perm.permission_level = level
        existing_perm.granted_by = current_user.id
        existing_perm.granted_at = utc_now()
        existing_perm.revoked_at = None  # Re-activate if it was revoked
        perm = existing_perm
    else:
        perm = DocumentPermission(
            id=generate_uuid(),
            document_id=document_id,
            user_id=target_user.id,
            permission_level=level,
            granted_by=current_user.id,
            granted_at=utc_now(),
            revoked_at=None
        )
        db.add(perm)

    db.commit()
    db.refresh(perm)

    # 5. Audit Logging
    log_audit_event(
        db=db,
        action="GRANT",
        status="ALLOWED",
        user_id=current_user.id,
        user_email=current_user.email,
        document_id=doc.id,
        document_title=doc.title,
        details=f"Granted {level} permission to {target_user.email}",
        request=request
    )

    out = PermissionOut.model_validate(perm)
    out.user_email = target_user.email
    return out

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def revoke_permission(
    document_id: str,
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Immediate Access Revocation Invariant:
    Revokes permission instantly. Any subsequent file fetch will fail immediately.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.owner_id != current_user.id:
        log_audit_event(
            db=db,
            action="DENIED_ACCESS",
            status="DENIED",
            user_id=current_user.id,
            user_email=current_user.email,
            document_id=doc.id,
            document_title=doc.title,
            details=f"Unauthorized attempt to revoke permissions by {current_user.role} {current_user.email}",
            request=request
        )
        raise HTTPException(status_code=403, detail="Only the document owner can revoke permissions")

    perm = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == user_id,
        DocumentPermission.revoked_at == None
    ).first()

    if not perm:
        raise HTTPException(status_code=404, detail="Active permission record not found")

    target_user = db.query(User).filter(User.id == user_id).first()
    target_email = target_user.email if target_user else "unknown"

    # Mark as revoked immediately
    perm.revoked_at = utc_now()
    db.commit()

    log_audit_event(
        db=db,
        action="REVOKE",
        status="ALLOWED",
        user_id=current_user.id,
        user_email=current_user.email,
        document_id=doc.id,
        document_title=doc.title,
        details=f"Revoked permission for user {target_email}. Takes effect immediately.",
        request=request
    )

    return {"message": f"Access for user {target_email} revoked immediately."}

@router.get("", response_model=List[PermissionOut])
def list_permissions(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.owner_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")

    perms = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.revoked_at == None
    ).all()

    results = []
    for p in perms:
        u = db.query(User).filter(User.id == p.user_id).first()
        out = PermissionOut.model_validate(p)
        out.user_email = u.email if u else "unknown"
        results.append(out)

    return results

