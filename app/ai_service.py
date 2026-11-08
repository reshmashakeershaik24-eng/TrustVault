import os
import json
import httpx
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, Document, AiSuggestion, generate_uuid, utc_now
from app.audit import log_audit_event

def analyze_and_suggest_permissions(
    db: Session,
    document: Document,
    request=None
) -> List[AiSuggestion]:
    """
    AI Suggestion Engine with Strict Human-in-the-Loop Barrier.
    The machine NEVER widens access on its own.
    It creates PENDING suggestions that require explicit human approval.
    """
    # Find active viewers/users that aren't the owner
    eligible_users = db.query(User).filter(
        User.id != document.owner_id,
        User.is_active == True,
        User.role.in_(["VIEWER", "OWNER"])
    ).all()

    if not eligible_users:
        return []

    suggestions_data = []

    # Try calling Groq API if GROQ_API_KEY is configured
    if settings.GROQ_API_KEY:
        try:
            prompt = (
                f"You are an enterprise document security assistant. "
                f"Analyze this document: Title='{document.title}', Category='{document.category}', Filename='{document.file_name}'. "
                f"Available users to share with: {[u.email for u in eligible_users]}. "
                f"Suggest at most 2 users who should legitimately have 'READ' access, with a 1-sentence rationale. "
                f"Return valid JSON only in this format: [{{\"email\": \"...\", \"permission\": \"READ\", \"rationale\": \"...\"}}]"
            )
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            with httpx.Client(timeout=5.0) as client:
                res = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"].strip()
                    # extract json array
                    start = content.find("[")
                    end = content.rfind("]") + 1
                    if start != -1 and end != -1:
                        suggestions_data = json.loads(content[start:end])
        except Exception:
            # Fall back to heuristic rule-based suggestion on error/timeout
            suggestions_data = []

    # Smart Heuristic Fallback if Groq is not configured or failed
    if not suggestions_data:
        cat_lower = (document.category or "").lower()
        title_lower = document.title.lower()

        for user in eligible_users:
            email_lower = user.email.lower()
            role_hint = email_lower.split("@")[0]

            matched = False
            rationale = ""

            if ("finan" in cat_lower or "salary" in title_lower or "budget" in title_lower) and ("finance" in role_hint or "viewer" in role_hint):
                matched = True
                rationale = f"Suggested because user appears relevant to Financial/Budget classification."
            elif ("legal" in cat_lower or "contract" in title_lower or "nda" in title_lower) and ("legal" in role_hint or "viewer" in role_hint):
                matched = True
                rationale = f"Suggested because user role matches Legal/Contract compliance review."
            elif ("hr" in cat_lower or "payroll" in title_lower) and ("hr" in role_hint or "viewer" in role_hint):
                matched = True
                rationale = f"Suggested because user handles HR/Personnel documentation."
            elif len(suggestions_data) == 0:
                matched = True
                rationale = f"Suggested peer review based on document category '{document.category}'."

            if matched:
                suggestions_data.append({
                    "email": user.email,
                    "permission": "READ",
                    "rationale": rationale
                })
                if len(suggestions_data) >= 2:
                    break

    # Persist suggestions as PENDING (Never auto-grant!)
    created_suggestions = []
    for s in suggestions_data:
        target_user = db.query(User).filter(User.email == s["email"]).first()
        if not target_user:
            continue

        suggestion = AiSuggestion(
            id=generate_uuid(),
            document_id=document.id,
            suggested_user_id=target_user.id,
            suggested_permission=s.get("permission", "READ"),
            rationale=s.get("rationale", "AI contextual document classification suggestion"),
            status="PENDING",
            created_at=utc_now()
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        created_suggestions.append(suggestion)

        # Audit that AI suggested (without granting access)
        log_audit_event(
            db=db,
            action="AI_SUGGESTION_CREATED",
            status="ALLOWED",
            user_id=document.owner_id,
            user_email=document.owner.email if document.owner else None,
            document_id=document.id,
            document_title=document.title,
            details=f"AI suggested {suggestion.suggested_permission} access for {target_user.email}. Status: PENDING human approval.",
            request=request
        )

    return created_suggestions

