from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Document, DocumentPermission, AiSuggestion, generate_uuid, utc_now
from app.schemas import AiSuggestionOut, AiSuggestionDecision, PermissionOut
from app.security import get_current_user
from app.audit import log_audit_event

router = APIRouter(prefix="/ai", tags=["AI Suggestions"])

@router.get("/suggestions", response_model=List[AiSuggestionOut])
def get_pending_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch pending AI permission suggestions for documents owned by current user"""
    # Get user's documents
    user_doc_ids = db.query(Document.id).filter(
        Document.owner_id == current_user.id,
        Document.is_deleted == False
    ).subquery()

    suggestions = db.query(AiSuggestion).filter(
        AiSuggestion.document_id.in_(user_doc_ids),
        AiSuggestion.status == "PENDING"
    ).all()

    results = []
    for s in suggestions:
        target_u = db.query(User).filter(User.id == s.suggested_user_id).first()
        out = AiSuggestionOut.model_validate(s)
        out.suggested_user_email = target_u.email if target_u else "unknown"
        results.append(out)

    return results

@router.post("/suggestions/{suggestion_id}/decision")
def decide_suggestion(
    suggestion_id: str,
    decision_in: AiSuggestionDecision,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-Loop Decision Point:
    Only a verified document owner can approve or reject the AI suggestion.
    The machine never widens access automatically.
    """
    suggestion = db.query(AiSuggestion).filter(
        AiSuggestion.id == suggestion_id,
        AiSuggestion.status == "PENDING"
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Pending suggestion not found")

    doc = db.query(Document).filter(Document.id == suggestion.document_id).first()
    if not doc or (doc.owner_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this document")

    target_user = db.query(User).filter(User.id == suggestion.suggested_user_id).first()
    target_email = target_user.email if target_user else "unknown"

    now = utc_now()
    suggestion.decided_by = current_user.id
    suggestion.decided_at = now

    if decision_in.action == "APPROVE":
        suggestion.status = "APPROVED"

        # Check existing permission
        existing_perm = db.query(DocumentPermission).filter(
            DocumentPermission.document_id == doc.id,
            DocumentPermission.user_id == suggestion.suggested_user_id
        ).first()

        if existing_perm:
            existing_perm.permission_level = suggestion.suggested_permission
            existing_perm.revoked_at = None
            existing_perm.granted_by = current_user.id
            existing_perm.granted_at = now
        else:
            new_perm = DocumentPermission(
                id=generate_uuid(),
                document_id=doc.id,
                user_id=suggestion.suggested_user_id,
                permission_level=suggestion.suggested_permission,
                granted_by=current_user.id,
                granted_at=now,
                revoked_at=None
            )
            db.add(new_perm)

        db.commit()

        # Audit human approval of AI recommendation
        log_audit_event(
            db=db,
            action="AI_SUGGESTION_APPROVED",
            status="ALLOWED",
            user_id=current_user.id,
            user_email=current_user.email,
            document_id=doc.id,
            document_title=doc.title,
            details=f"Human owner approved AI suggestion: Granted {suggestion.suggested_permission} to {target_email}",
            request=request
        )

        return {"message": f"Suggestion APPROVED. Access granted to {target_email}."}

    else:
        suggestion.status = "REJECTED"
        db.commit()

        # Audit human rejection of AI recommendation
        log_audit_event(
            db=db,
            action="AI_SUGGESTION_REJECTED",
            status="ALLOWED",
            user_id=current_user.id,
            user_email=current_user.email,
            document_id=doc.id,
            document_title=doc.title,
            details=f"Human owner rejected AI suggestion to share with {target_email}",
            request=request
        )

        return {"message": f"Suggestion REJECTED. No access granted to {target_email}."}

