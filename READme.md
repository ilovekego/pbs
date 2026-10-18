# Murang'a County Public Services Board Portal & Mwananchi AI Agent

An AI-powered e-governance platform for the Murang'a County Government Public Service Board in Kenya.

The platform digitizes public service delivery through an online portal where citizens can report infrastructure problems, apply for Single Business Permits (SBP), submit county bursary applications, and communicate with administrative officers.

The integrated Mwananchi AI Agent guides users through service workflows, supports account registration, collects application details, and initiates supported portal transactions through backend actions.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Official Murang'a County Governance Knowledge Base](#2-official-muranga-county-governance-knowledge-base)
3. [System Architecture and AI Action Protocol](#3-system-architecture-and-ai-action-protocol)
4. [Technology Stack](#4-technology-stack)
5. [Database Schema](#5-database-schema)
6. [Environment Configuration](#6-environment-configuration)
7. [Local Installation and Setup Guide](#7-local-installation-and-setup-guide)
8. [Production Deployment Guide](#8-production-deployment-guide-heroku--postgresql)
9. [Default System Credentials](#9-default-system-credentials)
10. [Security and Compliance Standards](#10-security-and-compliance-standards)
11. [Software License](#11-software-license)

---

## 1. Executive Summary

The portal combines citizen-facing services, administrative workflows, and AI-assisted interactions in a single web application.

### Core Features

- **Mwananchi AI Agent:** Conducts multi-turn conversations, retains workflow state, collects required information, and initiates supported actions for account registration, service requests, permit applications, and bursary applications.
- **Service Request Management:** Allows citizens to report issues involving roads, streetlights, water, and sanitation, then communicate with administrative officers through ticket-based discussions.
- **Two-Way Ticket Communication:** Supports threaded conversations between citizens and county officers within individual service request records.
- **Authentication and Verification:** Supports six-digit SMS one-time passwords through the TalkSasa v3 API and transactional email delivery through the Resend API.
- **Digital County Services:** Provides workflows for infrastructure complaints, Single Business Permit applications, and county bursary applications.
- **Accessibility Controls:** Includes dynamic font scaling and high-contrast display options to improve usability for people with visual impairments.
- **Persistent Data Storage:** Uses PostgreSQL with SQLAlchemy connection pooling for persistent application data and supports multi-worker deployment through Gunicorn.

## 2. Official Murang'a County Governance Knowledge Base

The portal and Mwananchi AI Agent include a structured knowledge base covering county leadership, constituencies, and electoral wards.

The following information represents the governance data configured for the application and should be verified against current official records before production use.

| Governance Tier | Leadership and Electoral Details |
|---|---|
| Executive Leadership | Governor: H.E. Dr. Irungu Kang'ata; Deputy Governor: H.E. Stephen Munania |
| County Legislative | Senator: Hon. Joe Nyutu; Woman Representative: Hon. Betty Maina; Speaker: Hon. Johnson Mukuha |
| Constituencies (7) | Kiharu, Kangema, Mathioya, Maragua, Kandara, Gatanga, Kigumo |
| Electoral Wards (35) | Township, Mbiri, Gaturi, Mugoiri, Murarandia, Wangu, Muguru, Kanyenyaini, Rwathia, Gitugi, Kiru, Kamacharia, Nginda, Ichagaki, Makuyu, Kambiti, Kamahuha, Muthithi, Muruka, Ng'araria, Ruchu, Gaichanjiru, Kagundi-ini, Ithiru, Gatanga, Kihumbu-ini, Mugumo-ini, Kariara, Ithanga, Kakuzi Mitumburi, Kigumo, Kangari, Kinyona, Kahumbu, Kimorori Wempa |

---

## 3. System Architecture and AI Action Protocol

The application separates the citizen interface, Flask backend, database, and external communication services.

### Architecture Overview

```text
+--------------------------------------------------------------+
|                      CITIZEN FRONTEND                        |
|                                                              |
|  +----------------+  +----------------+  +----------------+  |
|  | Citizen        |  | Accessibility  |  | Mwananchi AI   |  |
|  | Dashboard      |  | Controls       |  | Assistant      |  |
|  +--------+-------+  +--------+-------+  +--------+-------+  |
+-----------|-------------------|--------------------|---------+
            |                   |                    |
            +-------------------+--------------------+
                                |
                                v
+--------------------------------------------------------------+
|                       FLASK BACKEND                          |
|                                                              |
|  +----------------+  +----------------+  +----------------+  |
|  | Authentication |  | Service Layer  |  | AI Action      |  |
|  | and Blueprints |  | and Validation |  | Parser         |  |
|  +--------+-------+  +--------+-------+  +--------+-------+  |
|           |                   |                    |         |
|           +-------------------+--------------------+         |
+-------------------------------|------------------------------+
                                |
              +-----------------+------------------+
              |                 |                  |
              v                 v                  v
+---------------------+ +------------------+ +------------------+
| PostgreSQL          | | TalkSasa SMS API | | Resend Email API |
| Persistent Storage  | | OTP Delivery     | | Email Delivery   |
+---------------------+ +------------------+ +------------------+
```

### AI Autonomous Action Tag Execution

Mwananchi AI follows a structured interaction process. It collects the information required for a supported workflow and returns an action tag that the backend can interpret.

The backend parses the action, validates the supplied data, executes the corresponding application operation, and removes the internal action tag before displaying the response to the user.

Supported action formats include:

**1. Account Registration**

```text
[ACTION:REGISTER_USER|FULL_NAME|EMAIL|NATIONAL_ID|PHONE|PASSWORD|CONSTITUENCY|WARD]
```

**2. Service Request Submission**

```text
[ACTION:CREATE_TICKET|CATEGORY_CODE|SPECIFIC_LOCATION|PROBLEM_DESCRIPTION]
```

**3. Single Business Permit Application**

```text
[ACTION:APPLY_PERMIT|BUSINESS_NAME|BUSINESS_TYPE|LOCATION]
```

**4. County Bursary Application**

```text
[ACTION:APPLY_BURSARY|STUDENT_NAME|INSTITUTION|AMOUNT]
```

These formats define the expected action payloads. The backend must validate every field, enforce authorization rules, and reject malformed or unauthorized requests before executing a transaction.

---

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.10+ |
| Web Framework | Flask 3.0.2 |
| Database | PostgreSQL |
| ORM | Flask-SQLAlchemy 3.1.1 |
| PostgreSQL Driver | psycopg2-binary 2.9.9 |
| Authentication | Flask-Login 0.6.3 |
| Password Security | Werkzeug password hashing |
| Frontend | HTML5, CSS3, Bootstrap 5.3.2 |
| Icons | Font Awesome 6.4.0 |
| SMS Integration | TalkSasa Bulk SMS API v3 |
| Email Integration | Resend API |
| WSGI Server | Gunicorn 21.2.0 |
| Deployment Platform | Heroku |
| Production Database Add-on | Heroku Postgres essential-0 |

---

## 5. Database Schema

The database organizes user accounts, service requests, ticket discussions, permit applications, and bursary applications.

### Entity Relationships

```text
                         +----------------------+
                         |         User         |
                         |----------------------|
                         | id (PK)              |
                         | full_name            |
                         | email (Unique)       |
                         | national_id (Unique) |
                         | phone (Unique)       |
                         | role                 |
                         +----------+-----------+
                                    |
                    +---------------+---------------+
                    |                               |
                    | 1:N                           | 1:N
                    v                               v
        +----------------------+        +----------------------+
        |   ServiceRequest     |        |   TicketComment      |
        |----------------------|        |----------------------|
        | id (PK)              |        | id (PK)              |
        | ticket_id (Unique)   |        | ticket_id (FK)       |
        | category_id (FK)     |        | message              |
        | status               |        | is_admin_reply       |
        | description          |        +----------------------+
        +----------------------+

        +----------------------+        +----------------------+
        |   BusinessPermit     |        |  BursaryApplication  |
        |----------------------|        |----------------------|
        | permit_number        |        | application_id       |
        | business_name        |        | student_name         |
        +----------------------+        +----------------------+
```

### Main Entities

- **User:** Stores account details, contact information, identity references, and user roles.
- **ServiceRequest:** Stores citizen complaints, ticket references, categories, descriptions, and request statuses.
- **TicketComment:** Stores messages associated with service request discussions, including administrative replies.
- **BusinessPermit:** Stores information associated with business permit applications.
- **BursaryApplication:** Stores student and application details for county bursary requests.

The diagram summarizes the main entities and their intended relationships. Exact foreign keys, constraints, and additional columns depend on the implemented SQLAlchemy models.

---

## 6. Environment Configuration

Create a `.env` file in the project root directory and configure the required environment variables.

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=generate_a_secure_random_key_here_min_32_characters

DATABASE_URL=sqlite:///database.db

TALKSASA_API_ENDPOINT=https://bulksms.talksasa.com/api/v3/sms/send
TALKSASA_API_TOKEN=your_talksasa_bearer_token_here
TALKSASA_SENDER_ID=TALK-SASA

RESEND_API_KEY=re_your_resend_api_key_here
MAIL_DEFAULT_SENDER="Murang'a County Portal <otp@muranga.go.ke>"
MAIL_RESET_SENDER="Murang'a County Portal <reset@muranga.go.ke>"

MWANANCHI_AI_ENDPOINT=https://api.vinniedigitalhub.co.ke/ai/gpt
```

### Configuration Notes

- Replace all placeholder credentials with valid values.
- Generate a strong, unpredictable `SECRET_KEY` before deployment.
- Keep API tokens and production credentials out of source control.
- The example uses SQLite for local development. Configure `DATABASE_URL` for PostgreSQL when running in production.
- Ensure the configured email sender domains are authorized by the email provider.
- Confirm that the Mwananchi AI endpoint is accessible and configured to return the action formats expected by the backend.
- Do not commit the `.env` file to a public repository.

---

## 7. Local Installation and Setup Guide

### Prerequisites

Install Python 3.10 or later and Git. Ensure the project dependencies are available before starting the application.

### Step 1: Clone the Repository

```bash
git clone https://github.com/ilovekego/pbs
cd pbs
```

### Step 2: Create a Virtual Environment

**Linux/macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create the `.env` file described in [Section 6](#6-environment-configuration) and supply the required development configuration.

### Step 5: Start the Application

```bash
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

The application is expected to initialize its database tables and default service categories on startup, provided that the initialization logic is implemented and configured correctly.

---

## 8. Production Deployment Guide (Heroku & PostgreSQL)

The following steps describe the intended deployment workflow using the Heroku CLI and a PostgreSQL add-on.

### Step 1: Install the Heroku CLI and Log In

```bash
heroku login
```

Create the application:

```bash
heroku create muranga-county-portal
```

### Step 2: Provision PostgreSQL

```bash
heroku addons:create heroku-postgresql:essential-0
```

Confirm that the database add-on has been provisioned successfully before proceeding.

### Step 3: Configure Production Environment Variables

```bash
heroku config:set SECRET_KEY="your_secure_production_secret_key"
```

Configure the TalkSasa API token:

```bash
heroku config:set TALKSASA_API_TOKEN="your_talksasa_token"
```

Configure the Resend API key:

```bash
heroku config:set RESEND_API_KEY="re_your_resend_api_key"
```

Set any additional production variables required by the application. Verify that the application reads the provisioned PostgreSQL connection URL and uses it instead of the local SQLite database.

### Step 4: Deploy the Application

Ensure the repository contains the required deployment configuration, including a valid `Procfile` and dependency definitions.

For a repository using the `master` deployment branch:

```bash
git push heroku master
```

If the local branch is named `main`, use the appropriate branch mapping instead.

### Step 5: Verify the Deployment

Check the deployment logs:

```bash
heroku logs --tail
```

Confirm that the application starts successfully, connects to PostgreSQL, and can access the configured external services.

**Production note:** The deployment commands assume that the Heroku application, database plan, build configuration, and required environment variables are available and correctly configured. Verify current platform requirements before deploying.

---

## 9. Default System Credentials

The following accounts are documented as default evaluation credentials. They should only be used if the corresponding accounts are actually seeded by the application.

| Role | Identifier / Email | Password | Scope and Privileges |
|---|---|---|---|
| County Administrator | `admin@muranga.go.ke` | `AdminPass123!` | Analytics, status management, ticket replies |
| Registered Citizen | `jane@citizen.go.ke` | `CitizenPass123!` | Service requests, permit applications, bursary applications |

These credentials are provided for local evaluation and testing only.

Before exposing the application publicly, replace or disable default accounts, enforce appropriate password policies, and verify role-based access controls. Never reuse evaluation passwords in production.

---

## 10. Security and Compliance Standards

The application is designed around the following security measures.

### Password Hashing

User passwords should be stored as secure password hashes rather than plaintext. The implementation uses Werkzeug security utilities, with the configured hashing method determining the actual algorithm.

### SQL Injection Prevention

SQLAlchemy ORM parameterization helps protect database operations from SQL injection. Raw SQL queries, where used, must also employ safe parameter binding.

### Authentication and Login Identifiers

The application supports login using an email address, national ID, or international-format phone number such as `254XXXXXXXXX`, according to the configured authentication logic.

### File Upload Validation

File uploads are restricted to approved image formats:

- PNG
- JPG
- JPEG
- WEBP

Validation should check file contents as well as extensions and MIME types. File size limits, safe filenames, and appropriate storage permissions should also be enforced.

### Authorization and Transaction Validation

Backend operations must verify user roles, ownership, and permissions before allowing service requests, permit applications, bursary submissions, or administrative actions.

AI-generated action tags must be treated as untrusted input. Validate all values on the server, prevent duplicate transactions, and avoid executing privileged operations solely because an AI response contains an action tag.

### Sensitive Configuration

API tokens, database credentials, and application secrets must be supplied through environment variables or an appropriate secrets manager. Production secrets should never be committed to the repository.

### Accessibility

The interface includes font scaling and high-contrast controls intended to improve accessibility. Full WCAG 2.1 conformance requires testing the complete application against the relevant success criteria; individual accessibility features alone do not establish compliance.

---

## 11. Software License

Copyright 2026 Murang'a County Government Public Service Board.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License.

You may obtain a copy of the License at:

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and limitations under the License.
