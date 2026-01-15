"""
Invoice Management Routes
"""
import logging
import uuid
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

logger = logging.getLogger(__name__)

from src.models import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceStatus, SuccessResponse, User, InvoiceGenerateRequest, JiraTicket, TicketStatus
from src.database import get_db, InvoiceRepository, AuditRepository
from src.services.jira_integration import JiraIntegrationService
from src.services.invoice_generator import InvoiceGenerator
from configs.config import config
from .dependencies import get_current_user, get_admin_user
from .converters import convert_invoice_model


def register_routes(app: FastAPI):
    """Register invoice routes"""
    
    @app.get("/api/invoices", response_model=List[Invoice], tags=["Invoices"])
    async def list_invoices(
        status: InvoiceStatus = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """List all invoices with optional status filter"""
        invoice_repo = InvoiceRepository(db)
        if status:
            invoice_models = invoice_repo.get_by_status(status)
        else:
            invoice_models = invoice_repo.get_all()
        return [convert_invoice_model(im, db) for im in invoice_models]
    
    
    @app.post("/api/invoices", response_model=Invoice, status_code=status.HTTP_201_CREATED, tags=["Invoices"])
    async def create_invoice(
        invoice_data: InvoiceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Create a new invoice (Admin only)"""
        invoice_repo = InvoiceRepository(db)
        audit_repo = AuditRepository(db)

        # Generate unique invoice ID
        invoice_dict = invoice_data.dict()
        invoice_dict["invoice_id"] = str(uuid.uuid4())

        invoice_model = invoice_repo.create(invoice_dict)
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="CREATE_INVOICE",
            details=f"Created invoice {invoice_model.invoice_id} ({invoice_model.project_name})"
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

            # Create service instance with config
            token = "mock_token" if not current_user.has_jira_token else "mock_jira_token_for_" + current_user.user_id
            jira_service = JiraIntegrationService(
                api_endpoint=config.JIRA_API_ENDPOINT,
                user_token=token,
                db=db
            )

            # Step 1: Fetch and process tickets with date filtering
            logger.info(f"Step 1: Fetching tickets...")
            tickets = await jira_service.fetch_and_process_tickets(
                project_key=request.jira_project_key,
                status_filter=TicketStatus.CLOSED,
                label_filter=None,
                start_date=request.billing_period_start,
                end_date=request.billing_period_end
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


    @app.get("/api/invoices/{invoice_id}", response_model=Invoice, tags=["Invoices"])
    async def get_invoice(
        invoice_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get a specific invoice by ID"""
        invoice_repo = InvoiceRepository(db)
        invoice_model = invoice_repo.get(invoice_id)
        
        if not invoice_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return convert_invoice_model(invoice_model, db)
    
    
    @app.put("/api/invoices/{invoice_id}", response_model=Invoice, tags=["Invoices"])
    async def update_invoice(
        invoice_id: str,
        invoice_data: InvoiceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Update an invoice (Admin only)"""
        invoice_repo = InvoiceRepository(db)
        audit_repo = AuditRepository(db)
        
        invoice_model = invoice_repo.update(invoice_id, invoice_data.dict())
        
        if not invoice_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="UPDATE_INVOICE",
            details=f"Updated invoice {invoice_model.invoice_id} ({invoice_model.project_name})"
        )
        
        return convert_invoice_model(invoice_model, db)
    
    
    @app.delete("/api/invoices/{invoice_id}", response_model=SuccessResponse, tags=["Invoices"])
    async def delete_invoice(
        invoice_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Delete an invoice (Admin only)"""
        invoice_repo = InvoiceRepository(db)
        audit_repo = AuditRepository(db)
        
        success = invoice_repo.delete(invoice_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="DELETE_INVOICE",
            details=f"Deleted invoice {invoice_id}"
        )
        
        return SuccessResponse(
            message="Invoice deleted successfully",
            data={"invoice_id": invoice_id}
        )