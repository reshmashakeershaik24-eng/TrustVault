import hashlib
from app.config import settings
from app.database import SessionLocal, Base, engine
from app.models import User, Document, DocumentPermission, generate_uuid, utc_now
from app.security import get_password_hash
from app.audit import log_audit_event

def seed_database(db=None):
    """Seeds default accounts and demo documents for live evaluation"""
    close_db = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        # Load default demo password dynamically from environment
        seed_password = settings.DEFAULT_USER_PASSWORD
        seed_hashed_password = get_password_hash(seed_password)

        # 1. Create Default Users if not existing
        admin = db.query(User).filter(User.email == "admin@trustvault.com").first()
        if not admin:
            admin = User(
                id=generate_uuid(),
                email="admin@trustvault.com",
                hashed_password=seed_hashed_password,
                full_name="Sarah Connor (System Administrator)",
                role="ADMIN",
                is_active=True,
                created_at=utc_now()
            )
            db.add(admin)
        else:
            admin.hashed_password = seed_hashed_password

        owner = db.query(User).filter(User.email == "owner@trustvault.com").first()
        if not owner:
            owner = User(
                id=generate_uuid(),
                email="owner@trustvault.com",
                hashed_password=seed_hashed_password,
                full_name="Michael Scott (Document Owner)",
                role="OWNER",
                is_active=True,
                created_at=utc_now()
            )
            db.add(owner)
        else:
            owner.hashed_password = seed_hashed_password

        viewer = db.query(User).filter(User.email == "viewer@trustvault.com").first()
        if not viewer:
            viewer = User(
                id=generate_uuid(),
                email="viewer@trustvault.com",
                hashed_password=seed_hashed_password,
                full_name="Jim Halpert (Authorized Viewer)",
                role="VIEWER",
                is_active=True,
                created_at=utc_now()
            )
            db.add(viewer)
        else:
            viewer.hashed_password = seed_hashed_password

        unauthorized = db.query(User).filter(User.email == "unauthorized@trustvault.com").first()
        if not unauthorized:
            unauthorized = User(
                id=generate_uuid(),
                email="unauthorized@trustvault.com",
                hashed_password=seed_hashed_password,
                full_name="Dwight Schrute (External User)",
                role="VIEWER",
                is_active=True,
                created_at=utc_now()
            )
            db.add(unauthorized)
        else:
            unauthorized.hashed_password = seed_hashed_password

        db.commit()
        db.refresh(admin)
        db.refresh(owner)
        db.refresh(viewer)
        db.refresh(unauthorized)

        # 2. Seed Sample Confidential Documents
        doc1 = db.query(Document).filter(Document.title == "Q3 Executive Salary Compensation.pdf").first()
        if not doc1:
            dummy_content = b"%PDF-1.4 TrustVault Confidential Executive Compensation Report. For Internal Board Eyes Only."
            sha = hashlib.sha256(dummy_content).hexdigest()

            doc1 = Document(
                id=generate_uuid(),
                owner_id=owner.id,
                title="Q3 Executive Salary Compensation.pdf",
                category="FINANCIAL",
                file_name="salary_comp_2026.pdf",
                mime_type="application/pdf",
                file_size=len(dummy_content),
                file_data=dummy_content,
                file_hash=sha,
                is_deleted=False,
                created_at=utc_now()
            )
            db.add(doc1)
            db.commit()
            db.refresh(doc1)

            log_audit_event(
                db=db,
                action="UPLOAD",
                status="ALLOWED",
                user_id=owner.id,
                user_email=owner.email,
                document_id=doc1.id,
                document_title=doc1.title,
                details="Initial system seed document uploaded"
            )

            # Grant READ access to Jim (viewer)
            perm1 = DocumentPermission(
                id=generate_uuid(),
                document_id=doc1.id,
                user_id=viewer.id,
                permission_level="READ",
                granted_by=owner.id,
                granted_at=utc_now(),
                revoked_at=None
            )
            db.add(perm1)
            db.commit()

            log_audit_event(
                db=db,
                action="GRANT",
                status="ALLOWED",
                user_id=owner.id,
                user_email=owner.email,
                document_id=doc1.id,
                document_title=doc1.title,
                details=f"Granted READ permission to {viewer.email}"
            )

        doc2 = db.query(Document).filter(Document.title == "Project Titan Acquisition Agreement - NDA.pdf").first()
        if not doc2:
            dummy_content2 = b"%PDF-1.4 Project Titan NDA. Confidential Legal Agreement. Strictly Private."
            sha2 = hashlib.sha256(dummy_content2).hexdigest()

            doc2 = Document(
                id=generate_uuid(),
                owner_id=owner.id,
                title="Project Titan Acquisition Agreement - NDA.pdf",
                category="LEGAL",
                file_name="project_titan_nda.pdf",
                mime_type="application/pdf",
                file_size=len(dummy_content2),
                file_data=dummy_content2,
                file_hash=sha2,
                is_deleted=False,
                created_at=utc_now()
            )
            db.add(doc2)
            db.commit()
            db.refresh(doc2)

            log_audit_event(
                db=db,
                action="UPLOAD",
                status="ALLOWED",
                user_id=owner.id,
                user_email=owner.email,
                document_id=doc2.id,
                document_title=doc2.title,
                details="Confidential acquisition agreement uploaded (restricted access)"
            )

        # Log a refused attempt to seed the audit ledger
        log_audit_event(
            db=db,
            action="DENIED_ACCESS",
            status="DENIED",
            user_id=unauthorized.id,
            user_email=unauthorized.email,
            document_id=doc2.id if doc2 else None,
            document_title="Project Titan Acquisition Agreement - NDA.pdf",
            details="Unauthorized user attempted direct download without valid grant"
        )

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeding completed successfully.")
