from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime

from models import (
    User, UserCreate, UserUpdate,
    LegalClause, LegalClauseCreate, LegalClauseUpdate,
    JiraTicket, JiraFetchRequest, JiraFetchResponse,
    Invoice, InvoiceCreate, InvoiceGenerateRequest, InvoiceListItem,
    AuditLog, AuditLogFilter,
    SuccessResponse, ErrorResponse,
    UserRole, TicketStatus, InvoiceStatus,
    JiraTokenRequest
)
from database import db

# ============================================================================
# FASTAPI APP CONFIGURATION
# ============================================================================

app = FastAPI(
    title="Legal Billing System API",
    description="Automated billing system for Altran-BMW FLASH project",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# DEPENDENCY: MOCK AUTHENTICATION
# ============================================================================

async def get_current_user(user_id: str = "user_001") -> User:
    """Mock authentication - in production, validate JWT token"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user has admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Legal Billing System API",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/api/users/me", response_model=User, tags=["Users"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@app.get("/api/users", response_model=List[User], tags=["Users"])
async def list_users(
    current_user: User = Depends(get_admin_user)
):
    """List all users (Admin only)"""
    users = db.list_users()
    return users


@app.post("/api/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user)
):
    """Create a new user (Admin only)"""
    # Check if email already exists
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    user = db.create_user(user_data.dict())
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="CREATE_USER",
        details=f"Created user {user.user_id} ({user.email})"
    )
    
    return user


@app.put("/api/users/jira-token", response_model=SuccessResponse, tags=["Users"])
async def update_jira_token(
    token_request: JiraTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user's Jira Personal Access Token"""
    success = db.update_user_token(current_user.user_id, token_request.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update token"
        )
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="UPDATE_JIRA_TOKEN",
        details="Updated Jira PAT"
    )
    
    return SuccessResponse(
        message="Jira token updated successfully",
        data={"has_token": True}
    )


# ============================================================================
# LEGAL CLAUSE ENDPOINTS
# ============================================================================

@app.get("/api/clauses", response_model=List[LegalClause], tags=["Legal Clauses"])
async def list_clauses(
    active_only: bool = True,
    current_user: User = Depends(get_current_user)
):
    """List all legal clauses"""
    clauses = db.list_clauses(active_only=active_only)
    return clauses


@app.get("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
async def get_clause(
    clause_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific legal clause"""
    clause = db.get_clause(clause_id)
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found"
        )
    return clause


@app.post("/api/clauses", response_model=LegalClause, status_code=status.HTTP_201_CREATED, tags=["Legal Clauses"])
async def create_clause(
    clause_data: LegalClauseCreate,
    current_user: User = Depends(get_admin_user)
):
    """Create a new legal clause (Admin only)"""
    # Check if clause_id already exists
    existing_clause = db.get_clause(clause_data.clause_id)
    if existing_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clause {clause_data.clause_id} already exists"
        )
    
    clause = db.create_clause(clause_data.dict(), created_by=current_user.user_id)
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="CREATE_CLAUSE",
        details=f"Created clause {clause.clause_id}"
    )
    
    return clause


@app.put("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
async def update_clause(
    clause_id: str,
    clause_updates: LegalClauseUpdate,
    current_user: User = Depends(get_admin_user)
):
    """Update a legal clause (Admin only)"""
    clause = db.get_clause(clause_id)
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found"
        )
    
    updated_clause = db.update_clause(
        clause_id,
        clause_updates.dict(exclude_unset=True)
    )
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="UPDATE_CLAUSE",
        details=f"Updated clause {clause_id}"
    )
    
    return updated_clause


# ============================================================================
# JIRA INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/jira/fetch", response_model=JiraFetchResponse, tags=["Jira Integration"])
async def fetch_jira_tickets(
    request: JiraFetchRequest,
    current_user: User = Depends(get_current_user)
):
    """Fetch tickets from Jira (using mock data)"""
    # In production, this would call Jira API using user's PAT
    if not current_user.has_jira_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please configure your Jira Personal Access Token first"
        )
    
    # Get tickets from mock database
    tickets = db.get_jira_tickets(
        status=request.status_filter,
        label=request.label_filter
    )
    
    # Filter by date range (mock implementation)
    # In production, this would be part of the Jira API query
    
    billable_tickets = [t for t in tickets if t.is_billable]
    excluded_tickets = [t.ticket_id for t in tickets if not t.is_billable]
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="FETCH_JIRA_TICKETS",
        details=f"Fetched {len(tickets)} tickets, {len(billable_tickets)} billable"
    )
    
    return JiraFetchResponse(
        tickets=tickets,
        total_count=len(tickets),
        billable_count=len(billable_tickets),
        excluded_count=len(excluded_tickets),
        excluded_tickets=excluded_tickets
    )


@app.get("/api/jira/tickets", response_model=List[JiraTicket], tags=["Jira Integration"])
async def list_jira_tickets(
    status: Optional[TicketStatus] = None,
    label: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List Jira tickets with optional filters"""
    tickets = db.get_jira_tickets(status=status, label=label)
    return tickets


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.get("/api/invoices", response_model=List[InvoiceListItem], tags=["Invoices"])
async def list_invoices(
    current_user: User = Depends(get_current_user)
):
    """List all invoices for current user"""
    invoices = db.list_invoices(
        created_by=current_user.user_id if current_user.role != UserRole.ADMIN else None
    )
    
    # Convert to list items
    invoice_items = [
        InvoiceListItem(
            invoice_id=inv.invoice_id,
            project_name=inv.project_name,
            billing_period=inv.billing_period,
            total_amount=inv.total_amount,
            status=inv.status,
            created_at=inv.created_at,
            line_count=len(inv.lines)
        )
        for inv in invoices
    ]
    
    return invoice_items


@app.get("/api/invoices/{invoice_id}", response_model=Invoice, tags=["Invoices"])
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific invoice with all line items"""
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and invoice.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return invoice


@app.post("/api/invoices/generate", response_model=Invoice, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
async def generate_invoice(
    request: InvoiceGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a new invoice from Jira tickets"""
    # Fetch eligible tickets
    tickets = db.get_jira_tickets(status=TicketStatus.CLOSED)
    
    # Filter billable tickets
    billable_tickets = [t for t in tickets if t.is_billable and t.clause_id]
    
    if not billable_tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billable tickets found for the specified period"
        )
    
    # Create invoice lines
    lines = []
    for ticket in billable_tickets:
        clause = db.get_clause(ticket.clause_id)
        if not clause:
            continue
        
        line_data = {
            "jira_ticket_id": ticket.ticket_id,
            "clause_id": ticket.clause_id,
            "hours_worked": ticket.hours_worked,
            "unit_price": clause.unit_price
        }
        lines.append(line_data)
    
    # Create invoice
    invoice_data = {
        "project_name": request.project_name,
        "billing_period": request.billing_period,
        "total_amount": sum(
            line["hours_worked"] * line["unit_price"] for line in lines
        ),
        "currency": "EUR"
    }
    
    invoice = db.create_invoice(
        invoice_data=invoice_data,
        lines=lines,
        created_by=current_user.user_id
    )
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="GENERATE_INVOICE",
        details=f"Generated invoice {invoice.invoice_id} with {len(lines)} line items"
    )
    
    return invoice


@app.patch("/api/invoices/{invoice_id}/status", response_model=Invoice, tags=["Invoices"])
async def update_invoice_status(
    invoice_id: str,
    status: InvoiceStatus,
    current_user: User = Depends(get_current_user)
):
    """Update invoice status"""
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and invoice.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_invoice = db.update_invoice(invoice_id, {"status": status})
    
    # Log action
    db.create_audit_log(
        user_id=current_user.user_id,
        action="UPDATE_INVOICE_STATUS",
        details=f"Updated invoice {invoice_id} status to {status}"
    )
    
    return updated_invoice


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@app.get("/api/audit-logs", response_model=List[AuditLog], tags=["Audit"])
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """Get audit logs (Admin only)"""
    logs = db.get_audit_logs(user_id=user_id, action=action)
    return logs


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc)
        }
    )


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )