# TrustVault — Secure Document Sharing with a Real Audit Trail (RISE)

> **Timeline:** 7-Day Challenge  
> **Core Theme:** *"This is a security problem wearing the clothes of a CRUD application."*  
> **Mission:** Build a document platform where the wrong person can **never** read or access a file, and you can definitively **prove** who accessed it, when, and from where.

---

## 1. Executive Summary & Problem Context

In modern enterprises, sensitive documents (salary slips, NDAs, contracts, blueprints, regulatory audit records) are shared across employees, partners, and auditors. Conventional sharing tools fail drastically in two areas:

1. **Permission Creep & Zombie Access:** Folder-level permissions granting access to unwanted files, lingering access links after employee departure, or unintended cross-client visibility.
2. **Untraceable Breaches:** Inability to answer *"Who opened this file, and when?"* during an incident. An honest answer of *"we do not know"* causes catastrophic regulatory, legal, and client fallout.

**TrustVault** solves this by establishing server-enforced, immediate, and provably audited access controls.

---

## 2. The 3 Non-Negotiable Standards

Every design choice and endpoint must strictly satisfy these three foundational principles:

- [ ] **Standard 1: Server-Side Authorization Always**  
  Access control cannot rely on hidden UI elements, disabled buttons, or client-side guards. The backend server independently validates every single request, API route, and document streaming endpoint every time.
- [ ] **Standard 2: Verifiable & Immutable Audit Trail**  
  Every action—including failed/refused access attempts—must be immutably recorded. If an audit log can be silently altered or wiped, it is not evidence. The system must defend its log integrity.
- [ ] **Standard 3: Immediate Access Revocation**  
  Revoking a permission must take effect immediately. Any pre-issued tokens, shared links, active sessions, or cached permissions must terminate right at the moment of revocation.

---

## 3. Step-by-Step Implementation Roadmap & Checkpoints

### Phase 1: Authentication & Role-Based / Granular Access Control
- [ ] **Checkpoint 1.1 — User Authentication & Roles:**
  - Implement secure user sign-up, login, and session/token management.
  - Implement at least three clearly defined roles:
    - **Administrator:** System oversight, document audit view, user management.
    - **Document Owner:** Creator/uploader of documents with full management and sharing control.
    - **Viewer:** Consumer with view/read permissions granted by document owners.
  - Formally document the exact permission boundaries and role definitions.
- [ ] **Checkpoint 1.2 — Per-Document Named Permissions:**
  - Enable document owners to assign granular rights (`READ`, `EDIT`, `DOWNLOAD`, `MANAGE`) to specific named users.
  - Support instant permission revocation by the document owner or admin.
- [ ] **Checkpoint 1.3 — Strict Access Enforcement:**
  - Guarantee that unpermitted users cannot view metadata, download binaries, modify contents, or delete documents under any route.

---

### Phase 2: Document Management, Storage & Validation
- [ ] **Checkpoint 2.1 — Secure File Upload & Storage Isolation:**
  - Files must **not** be stored in a publicly accessible directory or exposed via static URLs.
  - Direct downloads must be mediated by authenticated, authorized server streaming or strictly time-limited, tightly scoped signed URLs.
- [ ] **Checkpoint 2.2 — Upload Validation & Content Verification:**
  - Validate file formats via MIME inspection and magic bytes (not just file extension).
  - Enforce strict size limits and sanitize file names to prevent directory traversal or remote code execution.
- [ ] **Checkpoint 2.3 — Metadata, Organization & Search:**
  - Organize files with categories, tags, or folder hierarchy.
  - Build search filters by **Document Name**, **Owner**, **Category**, and **Upload/Modified Date**.

---

### Phase 3: Tamper-Resistant Audit Trail & Admin Dashboard
- [ ] **Checkpoint 3.1 — Complete Event Logging:**
  - Log all document events: Uploads, Downloads, Views, Edits, Deletions, Permission Grants, and Revocations.
  - **Crucial:** Log **unauthorized access attempts (refused requests)** with user identity, timestamp, IP/client info, and requested resource.
- [ ] **Checkpoint 3.2 — Audit Trail Integrity:**
  - Protect logs from tampering (e.g., append-only database policies, cryptographic hashing / hash chains, or write-once storage).
- [ ] **Checkpoint 3.3 — Administrator Intelligence View:**
  - Provide an admin UI to monitor system-wide activity, suspicious anomalies, failed access spikes, and permission changes.

---

### Phase 4: AI Integration with Human-in-the-Loop Safeguards
- [ ] **Checkpoint 4.1 — Permitted AI Use Case:**
  - AI may be used as a recommendation assistant (e.g., suggesting which colleagues or departments need access based on document content/type).
- [ ] **Checkpoint 4.2 — Non-Negotiable AI Guardrail:**
  - **The machine must NEVER automatically widen access on its own.**
  - A human document owner must explicitly confirm any access recommendation.
  - Both the AI recommendation and the human confirmation decision must be logged in the audit trail.

---

### Phase 5: Automated Security Testing & Red-Team Defense
- [ ] **Checkpoint 5.1 — Automated Security Test Suite:**
  - Write test suites explicitly asserting that User B cannot access User A's private documents.
  - Verify boundary conditions: expired sessions, revoked tokens, direct URL guessing, IDOR (Insecure Direct Object Reference) attempts, and role privilege escalation.
- [ ] **Checkpoint 5.2 — Authorization Mutation Testing:**
  - Validate that removing or commenting out any backend authorization check immediately causes the automated test suite to fail.

---

## 4. Mandatory Project Deliverables

- [ ] **1. Public Git Repository:**
  - Clean commit history distributed across the 7 days (not a single monolithic dump at the end).
- [ ] **2. Live Deployed URL:**
  - Fully accessible deployment with pre-populated seed data.
  - Credentials in `README.md` for at least one account per role (Admin, Document Owner, Viewer).
- [ ] **3. `THREATS.md` Document:**
  - Comprehensive catalog of potential threat vectors considered.
  - Clear explanations of mitigations implemented.
  - Honest disclosure of trade-offs and knowingly accepted risks (with justification).
- [ ] **4. `PROMPTS.md` Log (Minimum 5 Dated Entries):**
  - Continuous log of AI tool prompts and iterations throughout the development week.
  - Each entry must detail:
    1. What you asked the AI tool to do (prompt or fair summary).
    2. What the AI produced.
    3. Exactly what was flawed, insecure, or wrong with the AI output.
    4. What you did instead, including links to git commits where the correction was implemented.
  - **Requirement:** At least two entries must specifically target **authorization, access control, or the audit trail**.
  - Include any reusable context files or system instructions used across the week.
- [ ] **5. Automated Test Suite:**
  - Tests covering the threat vectors cataloged in `THREATS.md`.
- [ ] **6. Database Schema & Setup Scripts:**
  - Reproducible setup instructions allowing the project to build and run cleanly from a fresh `git clone`.
- [ ] **7. Documented API Specifications:**
  - Document every endpoint along with explicit role and permission rules required to call it.
- [ ] **8. 5-Minute Demo Video:**
  - End-to-end walkthrough demonstrating permissions, immediate revocation, audit logging, and admin visibility.
- [ ] **9. Engineering Architecture Write-Up:**
  - Explanation of the chosen permission model in your own words.
  - What you deliberately chose *not* to build and why (simplicity and correctness beat bloated systems with security holes).
  - Reflection on AI utility vs. AI vulnerabilities and known unfinished gaps.

---

## 5. Scoring Rubric (100 Marks Total)

| Marks | Evaluation Category | Key Evaluation Criteria |
|:---:|:---|:---|
| **35** | **Security & Penetration Resistance** | Live red-teaming by judges against deployed system. *Note: Even one unauthorized document access failure forfeits most of this band!* |
| **15** | **Threat Thinking (`THREATS.md`)** | Depth of threat model against the evaluators' checklist, identification of non-obvious risks, and automated test alignment. |
| **15** | **Core Functionality** | Reliable execution of the 10 baseline product requirements. |
| **15** | **AI Direction & Quality Control (`PROMPTS.md`)** | Demonstration of active supervision, catching AI hallucinations/insecure patterns, and steering the tool. |
| **10** | **Engineering Quality** | Code readability, robust error handling, clean architectural modularity. |
| **10** | **Documentation, Deployment & Demo** | Clear deployment reproducibility, live URL reliability, informative 5-min demo video. |

---

## 6. Live Technical Interview Preparation Checkpoint

Shortlisted candidates must participate in a live technical walkthrough and live code modification:
- [ ] Walk through codebase architecture and defense boundaries.
- [ ] Identify the exact line of code where the authorization check occurs when a document is downloaded.
- [ ] Explain and demonstrate what happens if that authorization line is removed.
- [ ] Defend technology stack decisions, storage isolation, and revocation mechanics.

