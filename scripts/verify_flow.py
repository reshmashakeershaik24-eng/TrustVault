"""
Local End-to-End Verification Script
Tests the full system flow with sample document upload, authorization checks,
instant revocation, and audit ledger integrity verification.
"""
import os
import sys
import io

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def run_verification():
    print("=" * 60)
    print("Starting TrustVault End-to-End Flow Verification")
    print("=" * 60)

    auth_pwd = settings.DEFAULT_USER_PASSWORD

    # with TestClient(app) ensures FastAPI lifespan runs (DB init + seeder)
    with TestClient(app) as client:
        # 1. Login as Document Owner
        res_login = client.post("/api/auth/login", json={
            "email": "owner@trustvault.com",
            "password": auth_pwd
        })
        assert res_login.status_code == 200, f"Owner login failed: {res_login.text}"
        owner_token = res_login.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print("✔ Step 1: Document Owner authenticated successfully.")

        # 2. Upload Sample Confidential Document
        sample_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Confidential Strategic Roadmap 2026) >>\nendobj\ntrailer\n<< >>\n%%EOF"
        upload_file = io.BytesIO(sample_pdf_bytes)
        res_upload = client.post(
            "/api/documents/upload",
            headers=owner_headers,
            data={"title": "Confidential Strategic Roadmap 2026", "category": "FINANCIAL"},
            files={"file": ("Strategic_Roadmap_2026.pdf", upload_file, "application/pdf")}
        )
        assert res_upload.status_code == 201, f"Upload failed: {res_upload.text}"
        doc = res_upload.json()
        doc_id = doc["id"]
        print(f"✔ Step 2: Sample document uploaded: '{doc['title']}' (ID: {doc_id})")

        # 3. Unauthorized User Access Attempt (Red-Team Attack)
        res_unauth_login = client.post("/api/auth/login", json={
            "email": "unauthorized@trustvault.com",
            "password": auth_pwd
        })
        unauth_token = res_unauth_login.json()["access_token"]
        unauth_headers = {"Authorization": f"Bearer {unauth_token}"}

        res_forbidden = client.get(f"/api/documents/{doc_id}/download", headers=unauth_headers)
        assert res_forbidden.status_code == 403, "Security Flaw: Unauthorized user was not blocked!"
        print("✔ Step 3: Unauthorized user blocked with 403 Forbidden. Refusal logged to audit.")

        # 4. Owner Grants READ Permission to Authorized Viewer
        res_grant = client.post(
            f"/api/documents/{doc_id}/permissions",
            headers=owner_headers,
            json={"user_email": "viewer@trustvault.com", "permission_level": "READ"}
        )
        assert res_grant.status_code == 201, f"Permission grant failed: {res_grant.text}"
        granted_user_id = res_grant.json()["user_id"]
        print("✔ Step 4: READ permission granted to viewer@trustvault.com.")

        # 5. Viewer Downloads Document (Allowed)
        res_viewer_login = client.post("/api/auth/login", json={
            "email": "viewer@trustvault.com",
            "password": auth_pwd
        })
        viewer_token = res_viewer_login.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        res_download = client.get(f"/api/documents/{doc_id}/download", headers=viewer_headers)
        assert res_download.status_code == 200, f"Authorized viewer could not download: {res_download.text}"
        assert len(res_download.content) == len(sample_pdf_bytes), "Downloaded byte size mismatch"
        print(f"✔ Step 5: Authorized viewer downloaded file stream successfully ({len(res_download.content)} bytes).")

        # 6. Immediate Revocation Test
        res_revoke = client.delete(
            f"/api/documents/{doc_id}/permissions/{granted_user_id}",
            headers=owner_headers
        )
        assert res_revoke.status_code == 200, f"Permission revocation failed: {res_revoke.text}"
        print("✔ Step 6: Access revoked by document owner.")

        res_post_revoke = client.get(f"/api/documents/{doc_id}/download", headers=viewer_headers)
        assert res_post_revoke.status_code == 403, "CRITICAL ERROR: Revoked user still able to download!"
        print("✔ Step 7: Immediate Revocation verified: Subsequent download attempt instantly blocked with 403.")

        # 7. Admin Verifies Cryptographic Audit Ledger
        res_admin_login = client.post("/api/auth/login", json={
            "email": "admin@trustvault.com",
            "password": auth_pwd
        })
        admin_token = res_admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        res_verify = client.get("/api/audit/verify", headers=admin_headers)
        assert res_verify.status_code == 200, f"Verification endpoint failed: {res_verify.text}"
        verify_data = res_verify.json()
        assert verify_data["is_valid"] is True, f"Audit chain broken: {verify_data}"
        print(f"✔ Step 8: Cryptographic SHA-256 Audit Chain verified: 100% intact ({verify_data['verified_records']} records checked).")

    print("=" * 60)
    print("ALL LOCAL END-TO-END VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
