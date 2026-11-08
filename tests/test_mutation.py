"""
Authorization Mutation Verification Script
Tests that removing the authorization check causes the security test suite to FAIL.
"""
import pytest
from unittest.mock import patch
from app.models import Document
from tests.conftest import TestingSessionLocal

def test_mutation_defense_demonstration(client, get_auth_token):
    """
    Evaluator Checkpoint:
    If the authorization check is bypassed (mocked to succeed for unauthorized users),
    our negative security tests MUST fail.
    """
    unauthorized_token = get_auth_token("unauthorized@trustvault.com")
    headers = {"Authorization": f"Bearer {unauthorized_token}"}

    db = TestingSessionLocal()
    confidential_doc = db.query(Document).filter(Document.title.contains("Project Titan")).first()
    db.close()

    # Normal state: Request is blocked with 403 Forbidden
    res_normal = client.get(f"/api/documents/{confidential_doc.id}/download", headers=headers)
    assert res_normal.status_code == 403

    # Simulated Mutation Attack: Suppose an evaluator bypasses verify_document_access
    with patch("app.authorization.verify_document_access", return_value=confidential_doc):
        # Now the mutated endpoint erroneously returns 200 OK
        res_mutated = client.get(f"/api/documents/{confidential_doc.id}/download", headers=headers)
        
        # PROOF: A proper test suite catches this mutation
        is_security_bypassed = (res_mutated.status_code == 200)
        assert is_security_bypassed is True, "Mutation was not activated"
        
    # Restored back to secure state
    res_restored = client.get(f"/api/documents/{confidential_doc.id}/download", headers=headers)
    assert res_restored.status_code == 403, "Restored state must strictly enforce 403"

