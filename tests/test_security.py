import io
import pytest
from app.models import AuditLog, Document
from app.audit import verify_audit_chain
from tests.conftest import TestingSessionLocal

def test_unauthenticated_user_cannot_access_documents(client):
    """Attack 1: Accessing documents without bearer token must return 401"""
    res = client.get("/api/documents")
    assert res.status_code == 401

def test_idor_unauthorized_user_cannot_download_restricted_doc(client, get_auth_token):
    """
    Attack 2 (IDOR): Dwight (unauthorized user) tries to download 
    Michael's confidential Project Titan NDA document.
    Must return 403 Forbidden and record refused attempt in Audit Trail.
    """
    token_unauthorized = get_auth_token("unauthorized@trustvault.com")
    headers = {"Authorization": f"Bearer {token_unauthorized}"}

    # Locate the confidential document ID
    db = TestingSessionLocal()
    confidential_doc = db.query(Document).filter(Document.title.contains("Project Titan")).first()
    db.close()
    assert confidential_doc is not None

    res = client.get(f"/api/documents/{confidential_doc.id}/download", headers=headers)
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]

    # Verify that the refused attempt was immutably recorded in the Audit Log
    db = TestingSessionLocal()
    refused_log = db.query(AuditLog).filter(
        AuditLog.user_email == "unauthorized@trustvault.com",
        AuditLog.document_id == confidential_doc.id,
        AuditLog.action == "DENIED_ACCESS",
        AuditLog.status == "DENIED"
    ).first()
    db.close()
    assert refused_log is not None, "Crucial Non-Negotiable: Refused access attempt was NOT logged!"

def test_immediate_access_revocation_lifecycle(client, get_auth_token):
    """
    Standard 3: Taking access away works IMMEDIATELY.
    1. Owner grants Jim READ access -> Jim can download.
    2. Owner revokes Jim's access -> Jim's very next download attempt fails with 403!
    """
    owner_token = get_auth_token("owner@trustvault.com")
    viewer_token = get_auth_token("viewer@trustvault.com")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    db = TestingSessionLocal()
    confidential_doc = db.query(Document).filter(Document.title.contains("Project Titan")).first()
    db.close()

    # Step 1: Owner grants READ access to viewer
    grant_res = client.post(
        f"/api/documents/{confidential_doc.id}/permissions",
        headers=owner_headers,
        json={"user_email": "viewer@trustvault.com", "permission_level": "READ"}
    )
    assert grant_res.status_code == 201

    # Step 2: Viewer downloads successfully
    download_res1 = client.get(f"/api/documents/{confidential_doc.id}/download", headers=viewer_headers)
    assert download_res1.status_code == 200

    # Step 3: Owner IMMEDIATELY revokes access
    db = TestingSessionLocal()
    viewer_user_id = grant_res.json()["user_id"]
    db.close()

    revoke_res = client.delete(
        f"/api/documents/{confidential_doc.id}/permissions/{viewer_user_id}",
        headers=owner_headers
    )
    assert revoke_res.status_code == 200

    # Step 4: Viewer attempts download again - MUST FAIL IMMEDIATELY
    download_res2 = client.get(f"/api/documents/{confidential_doc.id}/download", headers=viewer_headers)
    assert download_res2.status_code == 403, "CRITICAL FLAW: Revoked user still able to download document!"

def test_executable_upload_blocked(client, get_auth_token):
    """Attack 3: Uploading malicious shell scripts or executables is rejected"""
    owner_token = get_auth_token("owner@trustvault.com")
    headers = {"Authorization": f"Bearer {owner_token}"}

    fake_payload = io.BytesIO(b"echo 'malicious script'")
    files = {"file": ("exploit.sh", fake_payload, "application/x-sh")}
    data = {"title": "Exploit Script", "category": "OPERATIONS"}

    res = client.post("/api/documents/upload", headers=headers, data=data, files=files)
    assert res.status_code == 400
    assert "forbidden" in res.json()["detail"].lower()

def test_audit_trail_tamper_detection(client, get_auth_token):
    """
    Standard 2: Proving who reached the file with a tamper-evident audit trail.
    If an attacker modifies a row or hash, verify_audit_chain MUST detect it!
    """
    db = TestingSessionLocal()
    # 1. Verify chain is valid initially
    res_clean = verify_audit_chain(db)
    assert res_clean["is_valid"] is True, "Clean audit chain should be valid"

    # 2. Simulate malicious attacker altering an existing audit log in the database
    target_log = db.query(AuditLog).first()
    original_action = target_log.action
    target_log.action = "TAMPERED_ACTION"
    db.commit()

    # 3. Chain verification must detect the forgery
    res_tampered = verify_audit_chain(db)
    assert res_tampered["is_valid"] is False, "Audit chain failed to detect row modification!"
    assert "Tampering detected" in res_tampered["message"]

    # Restore clean state
    target_log.action = original_action
    db.commit()
    db.close()

def test_ai_suggestion_requires_human_approval(client, get_auth_token):
    """
    Phase 4 Guardrail: Machine must NEVER widen access autonomously.
    A human owner must approve the suggestion.
    """
    owner_token = get_auth_token("owner@trustvault.com")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Upload document to trigger AI suggestion
    dummy_file = io.BytesIO(b"%PDF-1.4 Financial audit report 2026")
    files = {"file": ("financial_audit.pdf", dummy_file, "application/pdf")}
    data = {"title": "Annual Financial Audit 2026", "category": "FINANCIAL"}

    res = client.post("/api/documents/upload", headers=headers, data=data, files=files)
    assert res.status_code == 201
    doc_id = res.json()["id"]

    # Check pending suggestions
    sug_res = client.get("/api/ai/suggestions", headers=headers)
    assert sug_res.status_code == 200
    suggestions = sug_res.json()
    assert len(suggestions) > 0

    first_sug = suggestions[0]
    assert first_sug["status"] == "PENDING"

    # Unauthorized target user STILL cannot download (AI has not widened access)
    target_user_id = first_sug["suggested_user_id"]
    db = TestingSessionLocal()
    from app.models import DocumentPermission
    perm_check = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == doc_id,
        DocumentPermission.user_id == target_user_id
    ).first()
    db.close()
    assert perm_check is None, "AI automatically widened access without human approval!"

def test_admin_without_access_cannot_delete_document(client, get_auth_token):
    """
    Separation of Duties / Least Privilege:
    Admin cannot delete a private document unless granted access or ownership.
    Attempt must return 403 Forbidden and record refused attempt in Audit Trail.
    """
    admin_token = get_auth_token("admin@trustvault.com")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    db = TestingSessionLocal()
    confidential_doc = db.query(Document).filter(Document.title.contains("Project Titan")).first()
    db.close()
    assert confidential_doc is not None

    res = client.delete(f"/api/documents/{confidential_doc.id}", headers=admin_headers)
    assert res.status_code == 403, "Security Flaw: Admin without access was able to delete private document!"
    assert "Access Denied" in res.json()["detail"]

    # Verify refused attempt in audit log
    db = TestingSessionLocal()
    refused_log = db.query(AuditLog).filter(
        AuditLog.user_email == "admin@trustvault.com",
        AuditLog.document_id == confidential_doc.id,
        AuditLog.action == "DENIED_ACCESS",
        AuditLog.status == "DENIED"
    ).first()
    db.close()
    assert refused_log is not None, "Admin refused deletion attempt was not logged to audit trail!"

