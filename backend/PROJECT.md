# Legal Billing System

A FastAPI-based automated billing system for managing legal clause billing with Jira integration.

## Overview

This system automates the billing process for legal work tracked in Jira, mapping tickets to predefined legal clauses and generating invoices in multiple formats (PDF, Excel, SAP XML).

**Key Features:**
- Automated Jira ticket fetching and clause mapping
- Multi-format invoice generation (PDF, Excel, SAP XML)
- Role-based access control (Admin, Project Leader, Viewer)
- Comprehensive audit logging
- Interactive API documentation

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [API Documentation](#api-documentation)
5. [Release Notes](#release-notes)

---

## Installation

### Prerequisites
- Python 3.8+
- pip

### Steps
1. Clone the repository and navigate to the project directory

2. Create and activate virtual environment:
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # Linux/Mac: source venv/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

Start the development server:

```bash
python main.py
```

Access the application:
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

**Example: Generate Invoice**
```bash
curl -X POST "http://localhost:8000/api/invoices/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "BMW FLASH Project",
    "billing_period": "2024-12",
    "jira_project_key": "BMW"
  }'
```

---

## Configuration

Create a `.env` file with the following variables:

```env
DEBUG
SECRET_KEY
DATABASE_URL
JIRA_API_ENDPOINT
SSO_ENABLED
SSO_PROVIDER
```

**WARNING:** Never commit actual keys or credentials to version control.

---

## API Documentation

Once running, interactive documentation is available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

**Main Endpoints:**
- `GET /api/clauses` - List legal clauses
- `POST /api/jira/fetch` - Fetch Jira tickets
- `POST /api/invoices/generate` - Generate invoice
- `GET /api/audit-logs` - View audit trail

---

## Release Notes

### [v1.0.0] - 2024-01-13
#### 🚀 Added
- FastAPI-based REST API with auto-generated documentation
- Jira integration for ticket fetching
- Legal clause mapping engine
- Multi-format invoice generation (PDF, Excel, SAP XML)
- Role-based access control system
- Comprehensive audit logging
- Mock database with sample data for testing

#### 🛠 Changed
- N/A (Initial release)

#### 🐛 Fixed
- N/A (Initial release)