# TrustVault — Secure Document Sharing with a Real Audit Trail (RISE)

> **Core Philosophy:** *"This is a security problem wearing the clothes of a CRUD application."*  
> **Built for:** RISE 7-Day Security Challenge  
> **Stack:** Python 3.11, FastAPI, SQLite (Encrypted Embedded BLOB Storage), Vanilla/Tailwind Reactive UI

---

## 1. Demo Credentials & Roles (All Passwords Default to `1234`)

> **Notice:** Automatic login is disabled. All users must authenticate via email (ID) and password to access the platform.

The application strictly implements the **3 required roles** from the specification, plus an unshared viewer account for verification:

| Required Role | Email (ID) | Password | Allowed Capabilities |
|:---|:---|:---:|:---|
| **System Administrator** | `admin@trustvault.com` | `1234` | Full audit ledger view, cryptographic chain verification, system oversight. |
| **Document Owner** | `owner@trustvault.com` | `1234` | Upload confidential documents, grant/revoke user access, approve/reject AI suggestions. |
| **Viewer** | `viewer@trustvault.com` | `1234` | View and download documents explicitly granted by the document owner. |
| *Second Viewer (Unshared)* | `unauthorized@trustvault.com` | `1234` | Used in tests to demonstrate that unshared users cannot reach private documents (Requirement 5 & 10). |

### How to Sign In:
1. Open the application at [http://localhost:8000](http://localhost:8000) (or your live Render URL).
2. The **Authentication Gate** will require you to log in with an email and password.
3. Click any of the quick-fill role buttons to populate the respective email address, then enter the password (default: `1234`) into the password input field.
4. Click **Sign In**.

---

## 2. Local Setup & Running on Your Laptop

### Prerequisites
- Python 3.10+ installed
- Git installed

### Step 1: Clone and Navigate to Directory
```bash
cd e:/2026/sai_kiran/new_requirement
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
# On Windows PowerShell:
python -m venv venv
.\venv\Scripts\activate

# On Linux/macOS:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Open in Your Browser
- **Main Application & Document Explorer:** Open [http://localhost:8000](http://localhost:8000)
- **Administrative Audit Ledger & Tamper Verification:** Open [http://localhost:8000/admin](http://localhost:8000/admin)
- **Interactive Swagger API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs)

*(Note: On the first launch, the database `trustvault.db` is automatically created, schema applied, and pre-seeded with sample users, confidential documents, and initial audit entries!)*

---

## 3. How to Deploy to Render (100% Free)

You can deploy TrustVault to Render in less than 3 minutes:

### Option A: 1-Click Blueprint (Recommended & Simplest)
1. Ensure your latest code is pushed to your GitHub repository:
   ```bash
   git remote add origin https://github.com/<your-username>/TrustVault.git
   git push -u origin main
   ```
2. Log in to [Render.com](https://dashboard.render.com).
3. In the top navigation, click **New +** and select **Blueprint**.
4. Connect your GitHub repository: **`TrustVault`**.
5. Render will automatically read [`render.yaml`](file:///render.yaml), detecting:
   - Python runtime environment
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Pre-configured environment variables (`SECRET_KEY`, `DATABASE_URL`)
6. Click **Apply**.
7. Render will build the environment, apply migrations, and launch your service. Your live URL will be ready in ~2 minutes at `https://<service-name>.onrender.com`.

### Option B: Manual Web Service Deployment
If you prefer manual setup without Blueprint:
1. On [Render Dashboard](https://dashboard.render.com), click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository (`TrustVault`).
3. Fill in the deployment parameters:
   - **Name:** `trustvault` (or any custom name)
   - **Language:** `Python 3`
   - **Region:** Any (e.g. Oregon or Frankfurt)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free` (512 MB RAM, 0.1 CPU)
4. Under **Environment Variables**, click **Add Environment Variable**:
   - `SECRET_KEY` = `generate-any-secure-random-32-char-string`
   - `DATABASE_URL` = `sqlite:///./trustvault.db`
   - *(Optional)* `GROQ_API_KEY` = `<your-groq-key>` (Leave blank to use internal heuristic AI engine).
5. Click **Create Web Service**.
6. When deployment finishes, visit your live URL: `https://<your-service>.onrender.com`.

---

## 4. Running the Automated Security Tests & Mutation Defense

The evaluation explicitly verifies our security tests:
> *"We will take one authorisation check out of your code and run your tests. If they still pass, they were not testing anything."*

### Run All 8 Security Tests:
```bash
pytest tests/ -v
```

### What the 8 Tests Prove:
1. `test_unauthenticated_user_cannot_access_documents`: Assert 401 Unauthorized for unauthenticated calls.
2. `test_idor_unauthorized_user_cannot_download_restricted_doc`: Assert 403 Forbidden on IDOR attempts and verify refusal is logged to the audit ledger.
3. `test_immediate_access_revocation_lifecycle`: Assert that revoking permission cuts off download immediately within 0 ms.
4. `test_executable_upload_blocked`: Assert malicious scripts (`.sh`, `.exe`, `.bat`) are rejected with 400 Bad Request.
5. `test_audit_trail_tamper_detection`: Assert that modifying any audit record breaks the SHA-256 chain and fails verification.
6. `test_ai_suggestion_requires_human_approval`: Assert AI recommendations require explicit human approval and cannot auto-widen access.
7. `test_admin_without_access_cannot_delete_document`: Assert Admin cannot delete files without ownership or grant (Least Privilege).
8. `test_mutation_defense_demonstration`: Verifies that if `app/authorization.py:verify_document_access` is bypassed, the test suite catches it immediately.

---

## 5. API Documentation & Access Rules Matrix

| Method | Endpoint | Allowed Roles | Description & Authorization Rule |
|:---|:---|:---|:---|
| `POST` | `/api/auth/register` | Public | Register new user account. |
| `POST` | `/api/auth/login` | Public | Authenticate and obtain JWT token. Refused logins are audited. |
| `GET` | `/api/auth/me` | Authenticated | Retrieve current user profile. |
| `GET` | `/api/auth/users` | Authenticated | List active users for sharing dropdown. |
| `POST` | `/api/documents/upload` | `OWNER`, `ADMIN` | Upload document; stored safely as BLOB; triggers AI suggestions. |
| `GET` | `/api/documents` | Authenticated | List documents. Server returns **only** documents user is permitted to see. |
| `GET` | `/api/documents/{id}` | Permitted User | View document metadata. Gated by `verify_document_read_access`. |
| `GET` | `/api/documents/{id}/download` | Permitted User | **The Authorization Checkpoint:** Streams file bytes directly from DB. Gated by `verify_document_read_access`. |
| `DELETE` | `/api/documents/{id}` | Document Owner | Soft-deletes document. Admin/other users without edit access receive `403`. |
| `POST` | `/api/documents/{id}/permissions` | Document Owner | Grant `READ`/`EDIT` to named user email. Audited. |
| `DELETE` | `/api/documents/{id}/permissions/{user_id}` | Document Owner | **Immediate Revocation:** Terminates access immediately. |
| `GET` | `/api/audit` | `ADMIN` | View audit trail with search and filter. Non-admins receive `403`. |
| `GET` | `/api/audit/verify` | `ADMIN` | Cryptographic verification of SHA-256 hash chain from Genesis. |
| `GET` | `/api/ai/suggestions` | Document Owner | Fetch pending AI suggestions for owned documents. |
| `POST` | `/api/ai/suggestions/{id}/decision` | Document Owner | Human approval or rejection of AI suggestion. |
| `DELETE` | `/api/documents/{id}/permissions/{user_id}` | `OWNER`, `ADMIN` | **Immediate Revocation:** Terminates access immediately. |
| `GET` | `/api/audit` | `ADMIN` | View audit trail with search and filter. Non-admins receive `403`. |
| `GET` | `/api/audit/verify` | `ADMIN` | Cryptographic verification of SHA-256 hash chain from Genesis. |
| `GET` | `/api/ai/suggestions` | `OWNER`, `ADMIN` | Fetch pending AI suggestions for owned documents. |
| `POST` | `/api/ai/suggestions/{id}/decision` | `OWNER`, `ADMIN` | Human approval or rejection of AI suggestion. |

---

## 6. Architecture & Non-Negotiable Standards Defense

### 1. The Server Decides Every Time
- Route guards and client-side button hiding are solely for user convenience.
- Authorization is executed via FastAPI dependencies (`verify_document_read_access`) in [`app/authorization.py`](file:///app/authorization.py).
- Requests from curl, scripts, or Postman undergo identical validation against active database records.

### 2. Verifiable, Tamper-Evident Audit Trail
- Each entry in `audit_logs` is cryptographically linked to the previous entry:
  $$\text{Hash}_n = \text{SHA256}(\text{Hash}_{n-1} + \text{SeqId} + \text{Timestamp} + \text{UserId} + \text{DocId} + \text{Action} + \text{Status})$$
- If any entry is modified, deleted, or inserted out of order, `/api/audit/verify` flags the exact sequence ID where the chain was broken.
- **Refused attempts are logged:** Unauthorized downloads trigger `action="DENIED_ACCESS", status="DENIED"` with caller IP and timestamp.

### 3. Immediate Access Revocation
- Pre-signed S3 URLs and long-lived bearer tokens are avoided.
- File streaming reads permissions from the live database transaction.
- When an owner clicks "Revoke", the permission row receives `revoked_at = utc_now()`. Subsequent requests fail with `403 Forbidden` within 0 milliseconds.

---

## 7. Submission Artifacts
- [`THREATS.md`](file:///THREATS.md) — Detailed threat model, mitigations, and accepted trade-offs (15 Marks).
- [`PROMPTS.md`](file:///PROMPTS.md) — 5 dated supervision entries catching AI security mistakes with fixes (15 Marks).

