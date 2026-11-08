# PROMPTS.md — AI Supervised Engineering & Quality Oversight Log

> **Document Classification:** RISE Security Evaluation  
> **Target System:** TrustVault Document Platform  
> **Evaluation Weight:** 15 Marks  
> **Requirement:** At least 5 dated entries documenting prompt, flawed AI output, specific security analysis, and human correction. At least 2 entries focus directly on authorization, access control, or the audit trail.

---

### Entry 1: Architecture — Pre-Signed S3 URLs vs. Immediate Revocation
* **Date:** 2026-11-07
* **What I asked the tool to do:**  
  *"Design a scalable file download architecture for confidential documents using cloud storage."*
* **What it produced:**  
  The AI suggested generating pre-signed AWS S3 download URLs with an expiration time of 15 to 60 minutes whenever an authorized user requested a file.
* **What was wrong with it, specifically (Access Control Flaw):**  
  **Violates Non-Negotiable Standard #3 (Immediate Access Revocation).** Once a pre-signed S3 URL is minted, AWS S3 honors that URL until its expiry timestamp. If a document owner revokes a user's access 30 seconds later, the user can still download the file using the surviving pre-signed URL. Furthermore, S3 direct downloads bypass application-level audit logging, leaving no record of who actually executed the download.
* **What I did instead:**  
  I discarded pre-signed URLs entirely. I implemented a secure application-level streaming proxy (`app/routes/documents.py:download_document`). The server validates the live database permission record on every single chunk request and logs the download directly to the audit ledger before streaming bytes from SQLite BLOB storage.
* **Implementation Reference:** [`app/routes/documents.py`](file:///app/routes/documents.py) / Commit: `feat(security): enforce server-side streaming download over presigned URLs`

---

### Entry 2: Audit Trail — Standard Logging vs. Cryptographic Tamper-Evidence
* **Date:** 2026-11-07
* **What I asked the tool to do:**  
  *"Generate an audit logging model in SQLAlchemy to record document events."*
* **What it produced:**  
  The AI created a simple table with `id`, `user_id`, `action`, `timestamp`, and simple `logger.info()` console statements.
* **What was wrong with it, specifically (Audit Trail Integrity Flaw):**  
  **Violates Non-Negotiable Standard #2 (Verifiable Audit Trail).** A standard database table with plain rows can be quietly modified or truncated by anyone with SQL access (e.g., a rogue DBA or via SQL injection). The prompt explicitly states: *"An audit trail that can be quietly altered is not evidence, and we will ask you what stops that."* In addition, the AI failed to log refused attempts (`status = 'DENIED'`).
* **What I did instead:**  
  I designed a mathematical **SHA-256 Hash Chaining Ledger** (`app/audit.py`). Each row cryptographically binds the previous row's hash:
  $$\text{CurrentHash} = \text{SHA256}(\text{PreviousHash} + \text{SeqId} + \text{Timestamp} + \text{UserId} + \text{DocId} + \text{Action} + \text{Status})$$
  I also added the `/api/audit/verify` endpoint that recalculates the blockchain from Genesis, immediately exposing any altered or deleted row. Refused attempts were explicitly given first-class status with `action="DENIED_ACCESS", status="DENIED"`.
* **Implementation Reference:** [`app/audit.py`](file:///app/audit.py) / Commit: `feat(audit): implement SHA-256 hash chaining and tamper verification`

---

### Entry 3: Authorization — Client-Side Route Guards vs. Server-Side Invariants
* **Date:** 2026-11-07
* **What I asked the tool to do:**  
  *"Show how to restrict access so Viewers cannot see the document download button or call the endpoint."*
* **What it produced:**  
  The AI suggested hiding the download button in the frontend HTML using `v-if` / `*ngIf="user.role === 'OWNER'"` and adding a client-side route guard.
* **What was wrong with it, specifically (Client-Side Masking Flaw):**  
  **Violates Non-Negotiable Standard #1 (Server Decides Every Time).** The evaluation text warns: *"Not 'the button is hidden'. Not 'the page checks'. Through any route at all, including ones you did not think of. The server decides, every time."* Anyone using `curl` or Postman can bypass hidden UI buttons and directly hit `/api/documents/{id}/download`.
* **What I did instead:**  
  I built the server-side dependency `verify_document_read_access` in [`app/authorization.py`](file:///app/authorization.py). Regardless of what the UI displays, the FastAPI backend queries the live `document_permissions` table on the server. If the caller lacks active permissions, the server logs the refusal and returns `403 Forbidden`.
* **Implementation Reference:** [`app/authorization.py`](file:///app/authorization.py) / Commit: `feat(authz): enforce strict server-side dependency injection`

---

### Entry 4: AI Assistance — Autonomous Permission Widening vs. Human-in-the-Loop
* **Date:** 2026-11-07
* **What I asked the tool to do:**  
  *"Add an AI feature that automatically shares documents with relevant teammates upon upload."*
* **What it produced:**  
  The AI wrote an automated function that called an LLM, extracted email addresses, and directly executed `INSERT INTO document_permissions` to grant access automatically.
* **What was wrong with it, specifically (AI Autonomy Security Violation):**  
  **Violates Core AI Directive.** The problem statement explicitly mandates: *"The machine must never widen access on its own. A person confirms, and both the suggestion and the decision go into the audit."* An automated AI grant would enable prompt injection attacks (e.g., an uploaded file containing text ordering the AI to grant access to an external attacker).
* **What I did instead:**  
  I created a strict structural barrier: the AI service (`app/ai_service.py`) can only insert records into `ai_suggestions` with status `PENDING`. Only a verified human document owner can approve the suggestion via `POST /api/ai/suggestions/{id}/decision`. Both the AI suggestion and human decision are audited.
* **Implementation Reference:** [`app/ai_service.py`](file:///app/ai_service.py), [`app/routes/ai.py`](file:///app/routes/ai.py) / Commit: `feat(ai): enforce human-in-the-loop barrier on AI recommendations`

---

### Entry 5: File Validation — File Extension Trust vs. Header Validation
* **Date:** 2026-11-07
* **What I asked the tool to do:**  
  *"Write a file upload validation function for documents."*
* **What it produced:**  
  The AI checked `file.filename.endswith('.pdf')` and accepted the file.
* **What was wrong with it, specifically (Extension Spoofing & Remote Execution):**  
  Checking file extensions alone is trivially bypassed. An attacker can rename a shell script or malicious binary to `malicious.pdf` or upload `.sh` scripts if the check is not comprehensive.
* **What I did instead:**  
  I implemented multi-layer defense:
  1. Strict extension blacklist rejecting `.exe`, `.bat`, `.cmd`, `.sh`, `.php`, `.py`, `.ps1`.
  2. Storage of bytes as raw binary `BLOB` inside SQLite rather than writing executable files to the host OS filesystem.
  3. Forced download headers: `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`.
* **Implementation Reference:** [`app/routes/documents.py`](file:///app/routes/documents.py) / Commit: `fix(security): sanitize uploads and store in isolated database BLOB`

---

## 4. Reusable Context & System Prompts Used

```markdown
Role: Security-First Systems Architect
Standard Invariants:
1. Never trust the client. Enforce authorization on the backend server every time.
2. Every access and denied attempt must be logged in an immutable, cryptographically verifiable hash chain.
3. Access revocation must take effect immediately (zero token survivability).
4. AI must never automatically widen permissions; human approval is mandatory.
```

