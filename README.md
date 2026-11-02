# TrustVault — Secure Document Management System

## 1. Project Overview

TrustVault is a Secure Document Management System designed to store, manage, and access confidential documents securely. It aims to ensure that only authorized users can access permitted documents and maintains an audit trail to record document access activities.

This project is being developed as part of the **Snovasys Fresher Hiring Challenge 2026**.

## 2. Live Demo

- **Live Website:** https://trustvault-bplk.onrender.com/
- **GitHub Repository:** https://github.com/kalyani-chinta/TrustVault

## 3. Objectives

- Provide a secure platform for document management.
- Restrict document access according to user roles and permissions.
- Support role-based access control.
- Maintain an audit trail of document access activities.
- Provide a simple interface for users to interact with the system.

## 4. Key Features

### User Management
- User registration and account access.
- Role-based access for different user types.

### Role-Based Access Control (RBAC)

TrustVault is designed around the following roles:

- **Administrator:** Manages users and system-level activities.
- **Document Owner:** Manages their own documents and associated permissions.
- **Viewer:** Accesses only documents they are authorized to view.

### Document Management
- Provides an interface for managing documents.
- Supports access to documents based on permissions and user roles.
- Uses test documents for demonstration and evaluation.

### Audit Trail
- Records document access activities.
- Provides an Activity Log for authorized Admin users.

## 5. Technology Stack

- **Programming Language:** Java
- **Backend Framework:** Spring Boot
- **Security:** Spring Security
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **AI Integration:** Gemini API
- **Build Tool:** Maven
- **Deployment:** Render

## 6. Security Considerations

- Spring Security is used for application security.
- Role-based authorization is intended to restrict access to protected features.
- Database credentials and API keys should be configured through environment variables rather than committed to the repository.
- Users should upload only test documents while evaluating the application.

## 7. Running the Project Locally

### Prerequisites

Install the following:

- Java version compatible with the project configuration
- Maven, or use the included Maven Wrapper
- MySQL Server
- Git

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/kalyani-chinta/TrustVault.git
cd TrustVault
```

**2. Configure the database**

Create a MySQL database for the application and configure the database connection details in the project's application configuration.

**3. Configure environment variables**

Set the required environment variables according to the application's configuration, including:

- `DB_PASSWORD`
- `GEMINI_API_KEY`

Configure other database settings if required by the project. Do not commit actual passwords, API keys, or other secrets.

**4. Run the application on Windows**

```powershell
.\mvnw.cmd spring-boot:run
```

If the Maven Wrapper is unavailable, use an installed Maven setup.

**5. Open the application**

When running locally with the default Spring Boot port, visit:

http://localhost:8080

## 8. Demo Access

Evaluators can register an account through the live website to explore the available user features.

Administrator-only features, including the Activity Log, require an account with the appropriate Admin role. Verified administrator demo access can be provided separately if required.

Please use test documents only. Do not upload confidential or personal information.

## 9. Testing and Validation

The application can be evaluated by checking:

- User registration and account access.
- Availability of the document management interface.
- Access restrictions for different roles.
- Visibility of the Activity Log for authorized Admin users.
- Application behaviour on the deployed website.

Document upload, download, and the complete document lifecycle should be tested against the currently implemented functionality before being considered fully validated.

## 10. Project Status

TrustVault is an ongoing project. The deployed application provides an interface for demonstrating its available features. Some document management workflows and security scenarios may require further implementation, testing, and validation.

## 11. Future Enhancements

- Complete and validate document upload and download workflows.
- Improve document permission management.
- Expand audit logging and monitoring.
- Add further security testing.
- Improve error handling and user experience.

## 12. Repository Links

- **GitHub Repository:** https://github.com/kalyani-chinta/TrustVault
- **Live Demo:** https://trustvault-bplk.onrender.com/
