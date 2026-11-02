# TrustVault — Testing Report

## Overview

TrustVault was manually tested using the deployed web application and multiple test accounts. The goal was to verify the main document workflows and role-based access restrictions.

## Manual Test Results

| Test case | Expected result | Observed result |
|---|---|---|
| User registration and login | Registered users can log in | Passed |
| Document upload | User can upload a document | Passed |
| Saved document details | User can view saved document details | Passed |
| Document sharing | Owner can share a document with another registered user | Passed |
| Access revocation | Revoked user cannot reopen the shared document | Passed |
| Admin Activity Log | Viewer cannot access the Admin Activity Log | Passed |
| Independent user testing | Friends can use the deployed application | Successfully tested, according to manual testing |

## Testing Environment

- Application: Deployed TrustVault web application
- Testing method: Manual functional testing
- Accounts: Multiple test accounts, including owner and viewer roles
- Additional testing: Friends independently tested the live application

## Limitations

These results reflect the manual tests performed. Comprehensive adversarial security testing, automated test coverage, and production-level security validation have not yet been completed.

## Conclusion

The main document-management and access-control workflows passed the manual tests described above. Further security testing is needed before treating the application as production-ready.
