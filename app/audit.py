import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Request

from app.models import AuditLog, generate_uuid, utc_now

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def format_timestamp(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def calculate_hash(previous_hash: str, sequence_id: int, timestamp_str: str,
                   user_id: Optional[str], doc_id: Optional[str],
                   action: str, status: str, ip_address: Optional[str]) -> str:
    raw_payload = f"{previous_hash}|{sequence_id}|{timestamp_str}|{user_id or 'ANON'}|{doc_id or 'NONE'}|{action}|{status}|{ip_address or '0.0.0.0'}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

def log_audit_event(
    db: Session,
    action: str,
    status: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    document_id: Optional[str] = None,
    document_title: Optional[str] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None
) -> AuditLog:
    # 1. Extract IP & User Agent
    ip_address = request.client.host if request and request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown") if request else "Internal"

    # 2. Get last audit log to maintain hash chain
    last_log = db.query(AuditLog).order_by(AuditLog.sequence_id.desc()).first()
    if last_log:
        sequence_id = (last_log.sequence_id or 0) + 1
        prev_hash = last_log.current_hash
    else:
        sequence_id = 1
        prev_hash = GENESIS_HASH

    now = utc_now()
    timestamp_str = format_timestamp(now)

    # 3. Compute SHA-256 hash
    curr_hash = calculate_hash(
        previous_hash=prev_hash,
        sequence_id=sequence_id,
        timestamp_str=timestamp_str,
        user_id=user_id,
        doc_id=document_id,
        action=action,
        status=status,
        ip_address=ip_address
    )

    # 4. Save entry
    entry = AuditLog(
        id=generate_uuid(),
        sequence_id=sequence_id,
        user_id=user_id,
        user_email=user_email,
        document_id=document_id,
        document_title=document_title,
        action=action,
        status=status,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        previous_hash=prev_hash,
        current_hash=curr_hash,
        created_at=now
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def verify_audit_chain(db: Session) -> dict:
    logs = db.query(AuditLog).order_by(AuditLog.sequence_id.asc()).all()
    if not logs:
        return {
            "is_valid": True,
            "total_records": 0,
            "verified_records": 0,
            "broken_sequence_id": None,
            "message": "Audit trail is empty. Ready for events."
        }

    expected_prev = GENESIS_HASH
    for log in logs:
        # Check chain link
        if log.previous_hash != expected_prev:
            return {
                "is_valid": False,
                "total_records": len(logs),
                "verified_records": (log.sequence_id - 1),
                "broken_sequence_id": log.sequence_id,
                "message": f"Tampering detected at sequence {log.sequence_id}: Previous hash mismatch!"
            }

        # Check content integrity
        expected_curr = calculate_hash(
            previous_hash=log.previous_hash,
            sequence_id=log.sequence_id,
            timestamp_str=format_timestamp(log.created_at),
            user_id=log.user_id,
            doc_id=log.document_id,
            action=log.action,
            status=log.status,
            ip_address=log.ip_address
        )

        if log.current_hash != expected_curr:
            return {
                "is_valid": False,
                "total_records": len(logs),
                "verified_records": (log.sequence_id - 1),
                "broken_sequence_id": log.sequence_id,
                "message": f"Tampering detected at sequence {log.sequence_id}: Row payload was altered!"
            }

        expected_prev = log.current_hash

    return {
        "is_valid": True,
        "total_records": len(logs),
        "verified_records": len(logs),
        "broken_sequence_id": None,
        "message": "Cryptographic audit trail verified: 100% intact and untampered."
    }
