# TrustVault — Development Prompt Log

## 1. Project Overview

TrustVault is a web-based document management application developed using Java, Spring Boot, HTML, CSS, JavaScript, and MySQL.

The project focuses on user authentication, document ownership, controlled document sharing, access revocation, audit logging, and AI-assisted document question answering.

This log records development tasks, AI assistance, implementation decisions, issues encountered, testing performed, known limitations, and remaining work. Commit references are included where identified from the available Git history.

## 2. Development Log

### Entry 1 — 22 October 2026: Project Setup

- **Task:** Set up the Spring Boot project and configure database connectivity.
- **Tools:** ChatGPT, Spring Boot, Maven, and MySQL.
- **Issue:** Initial database connection and table-related errors prevented normal application startup.
- **Resolution:** Reviewed database configuration and startup settings, corrected the setup, and verified that the application could start.
- **Commit:** Exact commit reference not individually verified.

### Entry 2 — 22 October 2026: Registration and Password Security

- **Task:** Implement user registration and secure password storage.
- **Tool:** ChatGPT.
- **Issue:** Registration required database integration, validation, duplicate-email checks, and password hashing.
- **Resolution:** Implemented registration-related validation and BCrypt password hashing.
- **Testing:** Registration workflow was tested locally.
- **Commit:** Exact commit reference not individually verified.

### Entry 3 — 22 October 2026: Login and Session Handling

- **Task:** Implement login credential verification and maintain authenticated user information.
- **Tool:** ChatGPT.
- **Resolution:** Implemented BCrypt-based credential verification, session attributes for user identity and role, and logout functionality.
- **Commit:** [49ce2c9](https://github.com/kalyani-chinta/TrustVault/commit/49ce2c9)

### Entry 4 — 22 October 2026: Authorization and Role Checks

- **Task:** Add authorization checks for protected operations and administrator-only audit log access.
- **Tool:** ChatGPT.
- **Issue:** Returning a role in a login response does not, by itself, enforce authorization.
- **Resolution:** Added session-based checks for document operations and an administrator role check for the audit log endpoint.
- **Known limitation:** Authorization implementation requires further review and testing against unauthorized access attempts.
- **Commit:** [c75ed8d](https://github.com/kalyani-chinta/TrustVault/commit/c75ed8d)

### Entry 5 — 22 October 2026: Document Management and Audit Trail

- **Task:** Implement document creation, retrieval, ownership checks, and activity logging.
- **Tool:** ChatGPT.
- **Issue:** Authentication alone does not guarantee document-level authorization or provide an activity history.
- **Resolution:** Added document operations with ownership checks and audit records containing relevant user, document, action, and timestamp information.
- **Testing:** Document and audit workflows were exercised locally. The original development log reported successful Maven build and test results.
- **Commit:** [19144de](https://github.com/kalyani-chinta/TrustVault/commit/19144de)

### Entry 6 — 22 October 2026: HTTP Session Management

- **Task:** Maintain the authenticated user's identity between requests and support logout.
- **Tool:** ChatGPT.
- **Resolution:** Stored user-related information in the HTTP session after successful login and invalidated the session during logout.
- **Commit:** [49ce2c9](https://github.com/kalyani-chinta/TrustVault/commit/49ce2c9)

### Entry 7 — 23 October 2026: Document Management Interface

- **Task:** Create a browser interface for document management.
- **Tool:** ChatGPT.
- **Issue:** The document management page was initially unavailable at its intended URL.
- **Resolution:** Added the HTML page under Spring Boot static resources and restarted the application to load the updated resource.
- **Commit:** Exact commit reference not individually verified.

### Entry 8 — 23 October 2026: Project Documentation

- **Task:** Document project objectives, technology stack, setup, tested workflows, and remaining work.
- **Tool:** ChatGPT.
- **Resolution:** Prepared and updated the README with project information and local setup instructions.
- **Commit:** [4b7e6da](https://github.com/kalyani-chinta/TrustVault/commit/4b7e6da)

### Entry 9 — 24 October 2026: Document Sharing

- **Task:** Allow document owners to share documents with registered users.
- **Tool:** ChatGPT.
- **Issue:** Sharing required identifying the intended recipient and creating the correct document-sharing relationship.
- **Resolution:** Implemented a sharing workflow using the recipient's registered email address and recorded the sharing activity.
- **Testing:** Sharing was tested with a second registered account.
- **Commit:** [759c31a](https://github.com/kalyani-chinta/TrustVault/commit/759c31a)

### Entry 10 — 24 October 2026: Access Revocation

- **Task:** Allow owners to revoke previously granted document access.
- **Tool:** ChatGPT.
- **Issue:** The workflow needed to identify and remove the correct sharing record.
- **Resolution:** Added checks around the sharing record, removed the selected access grant, and recorded the revocation event.
- **Testing:** The recipient's document listing was checked after revocation.
- **Commit:** [759c31a](https://github.com/kalyani-chinta/TrustVault/commit/759c31a)

### Entry 11 — 24 October 2026: Audit Log Verification

- **Task:** Check whether important document activities were recorded.
- **Tools:** ChatGPT and a web browser.
- **Resolution:** Inspected audit log API responses and observed records for document creation, sharing, opening, and access revocation.
- **Known limitation:** Further authorization testing is required to ensure that unauthorized users cannot access protected audit information.
- **Commit:** [759c31a](https://github.com/kalyani-chinta/TrustVault/commit/759c31a)

### Entry 12 — 24 October 2026: AI Document Assistant

- **Task:** Integrate AI-powered question answering for accessible document content.
- **Tools:** ChatGPT and Google Gemini API.
- **Implementation:** Added an AI controller that accepts a document question, checks the logged-in user's document access, sends the relevant document content and question to the Gemini API, and parses the JSON response.
- **Testing:** Tested the AI endpoint locally and received a generated answer through the web interface.
- **Known limitations:** Responses depend on API credentials, network connectivity, model availability, and service limits. Generated answers may be inaccurate and should be reviewed.
- **Security consideration:** Further testing is needed to verify authorization boundaries and the handling of sensitive document content.
- **Commit:** [a3c7675](https://github.com/kalyani-chinta/TrustVault/commit/a3c7675)

### Entry 13 — 24 October 2026: Document File Handling

- **Task:** Add document file-handling support.
- **Tool:** ChatGPT.
- **Implementation:** Added a document file-handling service to the project.
- **Known limitation:** The presence of the service does not establish that every upload and download scenario has been fully validated. End-to-end testing, including file validation, access checks, and failure cases, remains necessary.
- **Commit:** [a3c7675](https://github.com/kalyani-chinta/TrustVault/commit/a3c7675)

### Entry 14 — 24 October 2026: README Improvement

- **Task:** Improve the project documentation and clarify implemented features, configuration, testing, and future work.
- **Tool:** ChatGPT.
- **Resolution:** Updated the README with project objectives, technology stack, setup instructions, AI integration, testing notes, and known limitations.
- **Commit:** [0b861f5](https://github.com/kalyani-chinta/TrustVault/commit/0b861f5)

## 3. Testing Summary

The following workflows were exercised locally during development:

- User registration and login.
- Document creation and retrieval.
- Sharing a document with another registered user.
- Revoking previously granted document access.
- Checking the recipient's document listing after revocation.
- Inspecting audit log records for document-related activities.
- Asking a question through the AI document interface and receiving a generated response.

These checks demonstrate the observed local behavior of the tested workflows. They do not establish comprehensive security, performance, or production readiness.

## 4. Known Limitations and Remaining Work

- Complete end-to-end testing of registration, login, logout, and document management.
- Test ownership and sharing permissions using multiple accounts, including unauthorized access attempts.
- Verify administrator and viewer permissions, particularly audit log authorization.
- Review session management, server-side authorization, and input validation.
- Validate file upload and download workflows, file types, file sizes, and unauthorized file access.
- Verify behavior when the AI service is unavailable or returns an error.
- Add or verify automated tests for authentication, document ownership, sharing, revocation, and audit log access.
- Confirm that the README instructions work in a clean environment.
- Deploy the application and validate the live URL, database connectivity, and core workflows.
- Complete the required Snovasys submission and verify its status.

## 5. Responsible AI Usage

ChatGPT was used as a development assistant for implementation guidance, troubleshooting, code explanations, and documentation preparation. Google Gemini API was integrated for AI-powered document question answering.

The application was tested locally for the workflows described in this document. AI assistance does not replace code review, security testing, or independent verification. Commit references and implementation history should be checked against the repository when needed.

## 6. Repository

GitHub repository: https://github.com/kalyani-chinta/TrustVault

Default working branch: `master`
