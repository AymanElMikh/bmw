from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from models import (
    User, UserCreate, UserUpdate,
    LegalClause, LegalClauseCreate, LegalClauseUpdate,
    JiraTicket, JiraFetchRequest, JiraFetchResponse,
    Invoice, InvoiceCreate, InvoiceGenerateRequest, InvoiceListItem,
    AuditLog, AuditLogFilter,
    SuccessResponse, ErrorResponse,
    UserRole, TicketStatus, InvoiceStatus, Currency,
    JiraTokenRequest
)
from database import (
    get_db, UserRepository, ClauseRepository, TicketRepository,
    InvoiceRepository, AuditRepository,
    UserRoleEnum, TicketStatusEnum, InvoiceStatusEnum, CurrencyEnum
)
from services.jira_integration import JiraIntegrationService
from services.mapping_engine import MappingEngine
from services.invoice_generator import InvoiceGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def convert_user_model(user_model) -> User:
    """Convert SQLAlchemy UserModel to Pydantic User"""
    if not user_model:
        return None
    return User(
        user_id=user_model.user_id,
        name=user_model.name,
        email=user_model.email,
        role=UserRole(user_model.role.value),
        has_jira_token=user_model.has_jira_token,
        created_at=user_model.created_at
    )


def convert_clause_model(clause_model) -> LegalClause:
    """Convert SQLAlchemy LegalClauseModel to Pydantic LegalClause"""
    if not clause_model:
        return None
    return LegalClause(
        clause_id=clause_model.clause_id,
        clause_name=clause_model.clause_name,
        description=clause_model.description,
        unit_price=clause_model.unit_price,
        currency=Currency(clause_model.currency.value),
        effective_date=clause_model.effective_date,
        expiry_date=clause_model.expiry_date,
        created_by=clause_model.created_by,
        created_at=clause_model.created_at,
        is_active=clause_model.is_active
    )


def convert_invoice_model(invoice_model, db: Session) -> Invoice:
    """Convert SQLAlchemy InvoiceModel to Pydantic Invoice"""
    from models import InvoiceLine
    
    lines = []
    for line_model in invoice_model.lines:
        line = InvoiceLine(
            line_id=line_model.line_id,
            invoice_id=line_model.invoice_id,
            jira_ticket_id=line_model.jira_ticket_id,
            clause_id=line_model.clause_id,
            hours_worked=line_model.hours_worked,
            unit_price=line_model.unit_price,
            line_total=line_model.line_total
        )
        lines.append(line)
    
    return Invoice(
        invoice_id=invoice_model.invoice_id,
        project_name=invoice_model.project_name,
        billing_period=invoice_model.billing_period,
        total_amount=invoice_model.total_amount,
        currency=Currency(invoice_model.currency.value),
        status=InvoiceStatus(invoice_model.status.value),
        created_by=invoice_model.created_by,
        created_at=invoice_model.created_at,
        lines=lines
    )


def convert_audit_log_model(log_model) -> AuditLog:
    """Convert SQLAlchemy AuditLogModel to Pydantic AuditLog"""
    if not log_model:
        return None
    return AuditLog(
        log_id=log_model.log_id,
        user_id=log_model.user_id,
        action=log_model.action,
        details=log_model.details,
        timestamp=log_model.timestamp
    )


# ============================================================================
# DEPENDENCY: AUTHENTICATION
# ============================================================================

async def get_current_user(user_id: str = "user_001", db: Session = Depends(get_db)) -> User:
    """Mock authentication - in production, validate JWT token"""
    user_repo = UserRepository(db)
    user_model = user_repo.get(user_id)
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return convert_user_model(user_model)


async def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """List all users (Admin only)"""
    user_repo = UserRepository(db)
    user_models = user_repo.get_all()
    return [convert_user_model(u) for u in user_models]


@app.post("/api/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new user (Admin only)"""
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    
    # Check if email already exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Convert role to enum
    user_dict = user_data.dict()
    user_dict['role'] = UserRoleEnum(user_data.role.value)
    
    user_model = user_repo.create(user_dict)
    
    # Log action
    audit_repo.log_action(
        user_id=current_user.user_id,
        action="CREATE_USER",
        details=f"Created user {user_model.user_id} ({user_model.email})"
    )
    
    return convert_user_model(user_model)


@app.put("/api/users/jira-token", response_model=SuccessResponse, tags=["Users"])
async def update_jira_token(
    token_request: JiraTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's Jira Personal Access Token"""
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    
    success = user_repo.update_jira_token(current_user.user_id, token_request.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update token"
        )
    
    # Log action
    audit_repo.log_action(
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all legal clauses"""
    clause_repo = ClauseRepository(db)
    
    if active_only:
        clause_models = clause_repo.get_active_clauses()
    else:
        clause_models = clause_repo.get_all()
    
    return [convert_clause_model(c) for c in clause_models]


@app.get("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
async def get_clause(
    clause_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific legal clause"""
    clause_repo = ClauseRepository(db)
    clause_model = clause_repo.get(clause_id)
    
    if not clause_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found"
        )
    
    return convert_clause_model(clause_model)


@app.post("/api/clauses", response_model=LegalClause, status_code=status.HTTP_201_CREATED, tags=["Legal Clauses"])
async def create_clause(
    clause_data: LegalClauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new legal clause (Admin only)"""
    clause_repo = ClauseRepository(db)
    audit_repo = AuditRepository(db)
    
    # Check if clause_id already exists
    existing_clause = clause_repo.get(clause_data.clause_id)
    if existing_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clause {clause_data.clause_id} already exists"
        )
    
    # Convert currency to enum
    clause_dict = clause_data.dict()
    clause_dict['currency'] = CurrencyEnum(clause_data.currency.value)
    clause_dict['created_by'] = current_user.user_id
    
    clause_model = clause_repo.create(clause_dict)
    
    # Log action
    audit_repo.log_action(
        user_id=current_user.user_id,
        action="CREATE_CLAUSE",
        details=f"Created clause {clause_model.clause_id}"
    )
    
    return convert_clause_model(clause_model)


@app.put("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
async def update_clause(
    clause_id: str,
    clause_updates: LegalClauseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update a legal clause (Admin only)"""
    clause_repo = ClauseRepository(db)
    audit_repo = AuditRepository(db)
    
    clause_model = clause_repo.get(clause_id)
    if not clause_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found"
        )
    
    updates = clause_updates.dict(exclude_unset=True)
    
    # Convert currency if present
    if 'currency' in updates and updates['currency']:
        updates['currency'] = CurrencyEnum(updates['currency'].value)
    
    updated_clause = clause_repo.update(clause_id, updates)
    
    # Log action
    audit_repo.log_action(
        user_id=current_user.user_id,
        action="UPDATE_CLAUSE",
        details=f"Updated clause {clause_id}"
    )
    
    return convert_clause_model(updated_clause)


# ============================================================================
# JIRA INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/jira/fetch", response_model=JiraFetchResponse, tags=["Jira Integration"])
async def fetch_jira_tickets(
    request: JiraFetchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch and process tickets from Jira
    This is the SINGLE endpoint for fetching tickets with billing info
    """
    try:
        logger.info(f"Fetching tickets for user {current_user.user_id}")
        logger.info(f"Request params: project={request.project_key}, status={request.status_filter}, label={request.label_filter}")
        
        # Create service instance with database session
        token = "mock_token" if not current_user.has_jira_token else "mock_jira_token_for_" + current_user.user_id
        jira_service = JiraIntegrationService(
            api_endpoint="https://jira.example.com",
            user_token=token,
            db=db
        )
        
        # Use the service to fetch and enrich tickets
        tickets = await jira_service.fetch_and_process_tickets(
            project_key=request.project_key,
            status_filter=request.status_filter,
            label_filter=request.label_filter,
            start_date=request.billing_period_start,
            end_date=request.billing_period_end
        )
        
        logger.info(f"Fetched {len(tickets)} tickets")
        
        # Separate billable and non-billable tickets
        billable_tickets = [t for t in tickets if t.is_billable]
        excluded_tickets = [t.ticket_id for t in tickets if not t.is_billable]
        
        logger.info(f"Billable: {len(billable_tickets)}, Excluded: {len(excluded_tickets)}")
        
        # Log action
        audit_repo = AuditRepository(db)
        audit_repo.log_action(
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
    
    except Exception as e:
        logger.error(f"Error fetching tickets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tickets: {str(e)}"
        )


@app.get("/api/jira/tickets", response_model=List[JiraTicket], tags=["Jira Integration"])
async def list_jira_tickets(
    status: Optional[TicketStatus] = None,
    label: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List Jira tickets with optional filters
    Always returns enriched tickets with billing information
    """
    # Create service instance (with or without token for mock)
    token = "mock_token" if not current_user.has_jira_token else "mock_jira_token_for_" + current_user.user_id
    jira_service = JiraIntegrationService(
        api_endpoint="https://jira.example.com",
        user_token=token,
        db=db
    )
    
    tickets = await jira_service.fetch_and_process_tickets(
        project_key="FLASH",  # Default project
        status_filter=status,
        label_filter=label,
        start_date=start_date,
        end_date=end_date
    )
    
    return tickets


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.get("/api/invoices", response_model=List[InvoiceListItem], tags=["Invoices"])
async def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all invoices for current user"""
    invoice_repo = InvoiceRepository(db)
    
    if current_user.role == UserRole.ADMIN:
        invoice_models = invoice_repo.get_all()
    else:
        invoice_models = invoice_repo.get_by_creator(current_user.user_id)
    
    invoice_items = [
        InvoiceListItem(
            invoice_id=inv.invoice_id,
            project_name=inv.project_name,
            billing_period=inv.billing_period,
            total_amount=inv.total_amount,
            status=InvoiceStatus(inv.status.value),
            created_at=inv.created_at,
            line_count=len(inv.lines)
        )
        for inv in invoice_models
    ]
    
    return invoice_items


@app.get("/api/invoices/{invoice_id}", response_model=Invoice, tags=["Invoices"])
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific invoice with all line items"""
    invoice_repo = InvoiceRepository(db)
    invoice_model = invoice_repo.get_with_lines(invoice_id)
    
    if not invoice_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and invoice_model.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return convert_invoice_model(invoice_model, db)


@app.post("/api/invoices/generate", response_model=Invoice, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
async def generate_invoice(
    request: InvoiceGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new invoice from Jira tickets for a specific period"""
    try:
        logger.info(f"=== Starting Invoice Generation ===")
        logger.info(f"User: {current_user.user_id}")
        logger.info(f"Project: {request.project_name}")
        logger.info(f"Billing Period: {request.billing_period}")
        
        # Check if request has project_key, start_date, end_date attributes
        project_key = getattr(request, 'project_key', 'FLASH')
        start_date = getattr(request, 'start_date', None)
        end_date = getattr(request, 'end_date', None)
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Create service instance with database session
        token = "mock_token" if not current_user.has_jira_token else "mock_jira_token_for_" + current_user.user_id
        jira_service = JiraIntegrationService(
            api_endpoint="https://jira.example.com",
            user_token=token,
            db=db
        )
        
        # Step 1: Fetch and process tickets with date filtering
        logger.info(f"Step 1: Fetching tickets...")
        tickets = await jira_service.fetch_and_process_tickets(
            project_key=project_key,
            status_filter=TicketStatus.CLOSED,
            label_filter=None,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Fetched {len(tickets)} tickets")
        
        # Step 2: Filter only billable tickets
        logger.info(f"Step 2: Filtering billable tickets...")
        billable_tickets = [t for t in tickets if t.is_billable and t.billable_amount > 0]
        logger.info(f"Found {len(billable_tickets)} billable tickets")
        
        if not billable_tickets:
            logger.warning("No billable tickets found!")
            for ticket in tickets:
                logger.info(f"  Ticket {ticket.ticket_id}: is_billable={ticket.is_billable}, amount={ticket.billable_amount}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billable tickets found for the specified period"
            )
        
        # Log billable tickets details
        for ticket in billable_tickets:
            logger.info(f"  ✓ {ticket.ticket_id}: {ticket.hours_worked}h × €{ticket.billable_amount/ticket.hours_worked} = €{ticket.billable_amount}")
        
        # Step 3: Generate invoice using the service
        logger.info(f"Step 3: Generating invoice...")
        invoice = InvoiceGenerator.generate_from_tickets(
            project_name=request.project_name,
            billing_period=request.billing_period,
            tickets=billable_tickets,
            created_by=current_user.user_id,
            db=db
        )
        logger.info(f"Invoice generated: {invoice.invoice_id}")
        logger.info(f"Total amount: €{invoice.total_amount}")
        logger.info(f"Line items: {len(invoice.lines)}")
        
        # Log action
        audit_repo = AuditRepository(db)
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="GENERATE_INVOICE",
            details=f"Generated invoice {invoice.invoice_id} with {len(invoice.lines)} line items"
        )
        
        logger.info(f"=== Invoice Generation Complete ===")
        return invoice
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice: {str(e)}"
        )


@app.patch("/api/invoices/{invoice_id}/status", response_model=Invoice, tags=["Invoices"])
async def update_invoice_status(
    invoice_id: str,
    status_update: InvoiceStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update invoice status"""
    invoice_repo = InvoiceRepository(db)
    audit_repo = AuditRepository(db)
    
    invoice_model = invoice_repo.get_with_lines(invoice_id)
    if not invoice_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and invoice_model.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update status
    status_enum = InvoiceStatusEnum(status_update.value)
    updated_invoice = invoice_repo.update_status(invoice_id, status_enum)
    
    # Log action
    audit_repo.log_action(
        user_id=current_user.user_id,
        action="UPDATE_INVOICE_STATUS",
        details=f"Updated invoice {invoice_id} status to {status_update.value}"
    )
    
    return convert_invoice_model(updated_invoice, db)


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@app.get("/api/audit-logs", response_model=List[AuditLog], tags=["Audit"])
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get audit logs (Admin only)"""
    audit_repo = AuditRepository(db)
    
    if user_id:
        log_models = audit_repo.get_by_user(user_id)
    elif action:
        log_models = audit_repo.get_by_action(action)
    else:
        log_models = audit_repo.get_recent(limit=100)
    
    logs = [convert_audit_log_model(log) for log in log_models]
    
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
# LIFESPAN EVENT
# ============================================================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    from database import init_db
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Application shutting down")


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