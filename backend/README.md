# Legal Billing System - FastAPI Implementation

A complete FastAPI-based automated billing system for managing legal clause billing with Jira integration.

## 🏗️ Architecture

This is a modular implementation with the following structure:

```
billing-system/
├── main.py              # FastAPI application & endpoints
├── models.py            # Pydantic schemas & data models
├── database.py          # Mock database with sample data
├── services.py          # Business logic services
├── config.py            # Application configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Documentation (Swagger UI)**: http://localhost:8000/api/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication & Users

- `GET /api/users/me` - Get current user info
- `GET /api/users` - List all users (Admin only)
- `POST /api/users` - Create new user (Admin only)
- `PUT /api/users/jira-token` - Update Jira PAT

### Legal Clauses

- `GET /api/clauses` - List all legal clauses
- `GET /api/clauses/{clause_id}` - Get specific clause
- `POST /api/clauses` - Create new clause (Admin only)
- `PUT /api/clauses/{clause_id}` - Update clause (Admin only)

### Jira Integration

- `POST /api/jira/fetch` - Fetch tickets from Jira
- `GET /api/jira/tickets` - List tickets with filters

### Invoices

- `GET /api/invoices` - List all invoices
- `GET /api/invoices/{invoice_id}` - Get invoice details
- `POST /api/invoices/generate` - Generate new invoice
- `PATCH /api/invoices/{invoice_id}/status` - Update invoice status

### Audit Logs

- `GET /api/audit-logs` - Get audit trail (Admin only)

## 🧪 Mock Data

The system comes pre-loaded with mock data:

### Users
- **John Doe** (PROJECT_LEADER) - `user_001`
- **Jane Smith** (ADMIN) - `user_002`
- **Bob Wilson** (VIEWER) - `user_003`

### Legal Clauses
- **FLASH_001**: Standard Development - €85.00/hour
- **FLASH_002**: Bug Fixing - €95.00/hour
- **FLASH_003**: Code Review - €75.00/hour
- **FLASH_004**: Technical Documentation - €70.00/hour

### Jira Tickets
- 6 sample tickets with various statuses
- Some billable, some not billable

### Sample Invoice
- Pre-generated invoice for December 2024
- Status: DRAFT
- Total: €2,462.50

## 🔧 Configuration

Edit `config.py` or create a `.env` file:

```env
# Application
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/billing_db

# Jira
JIRA_API_ENDPOINT=https://jira.bmw.com/rest/api/2

# SSO
SSO_ENABLED=True
SSO_PROVIDER=microsoft
```

## 📝 Example Usage

### 1. List Legal Clauses

```bash
curl -X GET "http://localhost:8000/api/clauses" \
  -H "accept: application/json"
```

### 2. Fetch Jira Tickets

```bash
curl -X POST "http://localhost:8000/api/jira/fetch" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "BMW",
    "billing_period_start": "2024-12-01T00:00:00Z",
    "billing_period_end": "2024-12-31T23:59:59Z",
    "status_filter": "CLOSED"
  }'
```

### 3. Generate Invoice

```bash
curl -X POST "http://localhost:8000/api/invoices/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "BMW FLASH Project",
    "billing_period": "2024-12",
    "jira_project_key": "BMW",
    "billing_period_start": "2024-12-01T00:00:00Z",
    "billing_period_end": "2024-12-31T23:59:59Z"
  }'
```

## 🏛️ Architecture Layers

### 1. **Models Layer** (`models.py`)
- Pydantic schemas for request/response validation
- Type safety and automatic documentation
- Business rules enforcement

### 2. **Database Layer** (`database.py`)
- Mock database for POC
- In production: Replace with SQLAlchemy ORM
- CRUD operations for all entities

### 3. **Services Layer** (`services.py`)
- **JiraIntegrationService**: Handles Jira API calls
- **MappingEngine**: Maps tickets to clauses
- **InvoiceGenerator**: Creates and exports invoices
- **AnalyticsService**: Generates reports

### 4. **API Layer** (`main.py`)
- FastAPI endpoints
- Authentication & authorization
- Error handling
- Request/response validation

## 🔐 Security Features

- **Authentication**: Mock authentication (ready for JWT/OAuth2)
- **Role-Based Access Control**: Admin, Project Leader, Viewer
- **Token Encryption**: Jira PATs stored encrypted
- **Audit Logging**: All actions tracked
- **Input Validation**: Pydantic models validate all inputs

## 📊 Export Formats

The system supports multiple export formats:

1. **PDF**: Professional invoice layout
2. **Excel**: BMW SAP-compatible format
3. **SAP XML**: Direct SAP integration format

## 🎯 Key Features

✅ Modular, clean architecture  
✅ Type-safe with Pydantic  
✅ Auto-generated API documentation  
✅ Mock data for testing  
✅ Role-based access control  
✅ Comprehensive audit logging  
✅ Multiple export formats  
✅ Error handling & validation  

## 🚧 Production Readiness

To make this production-ready, implement:

1. **Real Database**: Replace mock DB with PostgreSQL + SQLAlchemy
2. **Authentication**: Implement JWT tokens with Microsoft Entra ID/Okta
3. **Real Jira Integration**: Actual HTTP calls to Jira API
4. **File Storage**: S3/Azure Blob for invoice PDFs
5. **Email Notifications**: Send invoices via SMTP
6. **Rate Limiting**: Prevent API abuse
7. **Monitoring**: Add logging, metrics, and alerts
8. **Tests**: Unit and integration tests with pytest

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Both provide interactive API documentation where you can test all endpoints.

## 🤝 Contributing

This is a POC implementation. For production deployment:
1. Review security settings
2. Implement proper authentication
3. Add comprehensive error handling
4. Write tests (pytest)
5. Set up CI/CD pipeline

## 📄 License

Internal Altran/BMW Project - Confidential

---

**Questions?** Check the API documentation at `/api/docs` or review the code comments in each module.