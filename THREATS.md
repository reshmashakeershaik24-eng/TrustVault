\# TrustVault — Security Threat Model



\## 1. Purpose



This document identifies security threats relevant to TrustVault, a document management application with user authentication, document sharing, access revocation, audit logging, and an AI document assistant.



The threats below describe expected risks and security controls. A control must be verified through testing before it is considered effective.



\## 2. Assets to Protect



\- User accounts and passwords

\- Private document content and uploaded files

\- Document ownership and sharing permissions

\- Login sessions

\- Audit log records

\- Gemini API key and database credentials



\## 3. Threats and Mitigations



\### T1 — Unauthorized Document Access



\*\*Threat:\*\* A user may try to read another user's private document by changing a document ID or calling an API directly.



\*\*Mitigation:\*\* Verify the authenticated user's identity and document ownership or valid sharing permission on every document access request.



\*\*Test:\*\* Sign in as User A and create a private document. Sign in as User B and attempt to access User A's document through the UI and direct API request. Access must be denied.



\*\*Verification status:\*\* Requires explicit end-to-end testing.



\### T2 — Unauthorized Access After Revocation



\*\*Threat:\*\* A previously authorized recipient may continue accessing a document after the owner revokes sharing.



\*\*Mitigation:\*\* Check current sharing permissions on every protected request rather than relying on an old UI state or cached permission.



\*\*Test:\*\* Share a document with User B, confirm access, revoke the share as User A, then attempt to access the same document again as User B. Access must be denied.



\*\*Verification status:\*\* Requires end-to-end testing after revocation.



\### T3 — Authentication and Session Abuse



\*\*Threat:\*\* An unauthenticated user may call protected endpoints, or another person may misuse a stolen or improperly managed session.



\*\*Mitigation:\*\* Require authentication for protected endpoints, use secure session handling, and invalidate the session on logout. Production deployment should use HTTPS and appropriate cookie settings.



\*\*Test:\*\* Call protected endpoints without logging in, then log in and log out and retry using the old session. Protected access should be denied when unauthenticated.



\*\*Verification status:\*\* Requires systematic testing, including production cookie configuration.



\### T4 — Password Exposure



\*\*Threat:\*\* Passwords may be exposed if stored in plain text or accidentally included in logs or source control.



\*\*Mitigation:\*\* Hash passwords with BCrypt and never commit passwords, API keys, or database credentials to the repository.



\*\*Test:\*\* Register a test account and inspect the stored password value to confirm it is hashed. Search tracked files for secrets before publishing.



\*\*Verification status:\*\* BCrypt is part of the implementation; verify the stored value and scan the repository before submission.



\### T5 — Unauthorized Document Modification



\*\*Threat:\*\* A recipient or unrelated user may try to modify or delete a document they do not own or have permission to edit.



\*\*Mitigation:\*\* Enforce ownership and role-based authorization on every create, update, and delete operation.



\*\*Test:\*\* Sign in as User B and attempt to modify or delete User A's document through direct API requests. The request must be denied unless the documented permission explicitly allows it.



\*\*Verification status:\*\* Requires endpoint-by-endpoint testing.



\### T6 — Audit Log Tampering or Missing Events



\*\*Threat:\*\* Important document actions may not be recorded, or a user may try to alter another user's audit history.



\*\*Mitigation:\*\* Generate audit events on the server after validating the action. Restrict audit log access and do not trust client-submitted actor identities.



\*\*Test:\*\* Perform document access, sharing, and revocation operations and check that the expected actor, document, action, and timestamp are recorded. Attempt to access another user's logs.



\*\*Verification status:\*\* Requires testing against the implemented audit events and access rules.



\### T7 — Malicious or Oversized File Uploads



\*\*Threat:\*\* An attacker may upload an executable, unsupported, or excessively large file to exhaust storage or expose the server to unsafe content.



\*\*Mitigation:\*\* Validate file size, allowed file types, filenames, and storage paths. Store uploads outside publicly executable directories and prevent path traversal.



\*\*Test:\*\* Try an oversized file, an unsupported file type, a filename containing path traversal sequences, and a valid small file. Invalid uploads must be rejected safely.



\*\*Verification status:\*\* File-handling code exists, but upload/download validation and these security tests remain pending.



\### T8 — Secrets Exposure



\*\*Threat:\*\* Database credentials or the Gemini API key may be exposed through source code, Git history, logs, or public responses.



\*\*Mitigation:\*\* Load secrets from environment variables, exclude local secret files from Git, and never return secret values in API responses or logs.



\*\*Test:\*\* Inspect tracked files and repository history for credentials. Check application responses and logs for accidental secret disclosure.



\*\*Verification status:\*\* Environment-variable configuration is used; a complete secret scan is still required.



\### T9 — Prompt Injection and Sensitive Data Disclosure Through AI



\*\*Threat:\*\* Malicious document content or a user question may attempt to manipulate the AI assistant into revealing information beyond the user's authorization.



\*\*Mitigation:\*\* Verify document access on the server before sending content to the AI service. Send only the content needed for the request, treat document text as untrusted input, and do not rely on the model to enforce access control.



\*\*Test:\*\* Attempt to ask questions about a document the user cannot access. The server must reject the request before sending document content to the AI service. Also test malicious instructions embedded in an authorized test document.



\*\*Verification status:\*\* Access checks are implemented in the AI controller; additional prompt-injection and data-disclosure tests remain pending.



\### T10 — Cross-Site Scripting and Unsafe Input



\*\*Threat:\*\* Malicious input in document titles, content, or user-provided values may execute in a browser if rendered unsafely.



\*\*Mitigation:\*\* Validate input, encode untrusted content when rendering HTML, and avoid inserting untrusted values into the DOM as executable markup.



\*\*Test:\*\* Submit harmless XSS test strings such as `<script>alert(1)</script>` in supported fields and verify they are displayed as text rather than executed.



\*\*Verification status:\*\* Requires testing of all relevant UI rendering paths.



\## 4. General Security Testing Checklist



\- \[ ] Unauthenticated access to protected endpoints is denied.

\- \[ ] Users cannot access documents they neither own nor have permission to view.

\- \[ ] Revoked sharing permissions immediately prevent further access.

\- \[ ] Users cannot modify or delete documents without permission.

\- \[ ] Logout invalidates the session.

\- \[ ] Audit logs record required actions and enforce access restrictions.

\- \[ ] Upload validation rejects unsafe and oversized files.

\- \[ ] No credentials or API keys are committed or exposed.

\- \[ ] AI requests enforce authorization before document content is sent.

\- \[ ] Untrusted input is safely rendered in the browser.



\## 5. Limitations and Honest Status



This document is a threat model and test plan, not proof that every control is secure. Some controls are implemented in the current application, but the tests above have not all been completed or independently verified.



File upload/download validation, systematic authorization testing, prompt-injection testing, secret scanning, and production deployment security checks remain areas for verification.



Only mark a checklist item complete after running the corresponding test and recording the result.



\## 6. Responsible Disclosure



Do not test against other users' private data or systems without authorization. Use dedicated test accounts and non-sensitive sample documents. Report discovered vulnerabilities responsibly and avoid including secrets or private document contents in reports.

