"""
Jira Integration Routes
"""
import logging
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.models import JiraTicket, JiraFetchRequest, JiraFetchResponse, TicketStatus, User
from src.database import get_db, AuditRepository
from src.services.jira_integration import JiraIntegrationService
from configs.config import config
from .dependencies import get_current_user

logger = logging.getLogger(__name__)


def register_routes(app: FastAPI):
    """Register Jira integration routes"""
    
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
            
            # Get user's Jira token
            token = "mock_token" if not current_user.has_jira_token else f"mock_jira_token_for_{current_user.user_id}"
            
            # Create service instance
            jira_service = JiraIntegrationService(
                api_endpoint=config.JIRA_API_ENDPOINT,
                user_token=token,
                db=db
            )
            
            # Fetch and enrich tickets
            tickets = await jira_service.fetch_and_process_tickets(
                project_key=request.project_key,
                status_filter=request.status_filter,
                label_filter=request.label_filter,
                start_date=request.billing_period_start,
                end_date=request.billing_period_end
            )
            
            logger.info(f"Fetched {len(tickets)} tickets")
            
            # Separate billable and non-billable
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
        token = "mock_token" if not current_user.has_jira_token else f"mock_jira_token_for_{current_user.user_id}"
        
        jira_service = JiraIntegrationService(
            api_endpoint=config.JIRA_API_ENDPOINT,
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