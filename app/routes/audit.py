from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AuditLog
from app.schemas import AuditLogOut, AuditVerificationResult
from app.security import require_admin
from app.audit import verify_audit_chain

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_trail(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    status: Optional[str] = None,
    user_email: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Administrative view of all system activities, uploads, downloads,
    permission changes, and blocked access attempts.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if status:
        query = query.filter(AuditLog.status == status.upper())
    if user_email:
        query = query.filter(AuditLog.user_email.ilike(f"%{user_email}%"))

    return query.order_by(AuditLog.sequence_id.desc()).limit(limit).all()

@router.get("/verify", response_model=AuditVerificationResult)
def verify_audit_ledger(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Cryptographic verification of the SHA-256 hash chain.
    Proves whether the audit trail has been altered, rows deleted, or links forged.
    """
    result = verify_audit_chain(db)
    return AuditVerificationResult(**result)

