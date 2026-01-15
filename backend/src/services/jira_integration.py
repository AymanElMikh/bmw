from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models import JiraTicket, TicketStatus
from src.database import TicketRepository, ClauseRepository
from src.database.models import TicketStatusEnum
from .mapping_engine import MappingEngine


class JiraIntegrationService:
    """Service for interacting with Jira API and enriching tickets"""
    
    def __init__(self, api_endpoint: str, user_token: str, db: Session):
        self.api_endpoint = api_endpoint
        self.user_token = user_token
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.clause_repo = ClauseRepository(db)
    
    async def fetch_and_process_tickets(
        self,
        project_key: str,
        status_filter: Optional[TicketStatus] = None,
        label_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[JiraTicket]:
        """
        Fetch tickets from Jira API and enrich them with billing information
        This is the SINGLE source of truth for fetching tickets
        """
        # Step 1: Fetch raw tickets from database (in production, from Jira API)
        if status_filter:
            status_enum = TicketStatusEnum(status_filter.value)
            ticket_models = self.ticket_repo.get_by_status(status_enum)
        elif label_filter:
            ticket_models = self.ticket_repo.get_by_label(label_filter)
        else:
            ticket_models = self.ticket_repo.get_all()
        
        # Convert to Pydantic models
        tickets = [self._convert_ticket_model(t) for t in ticket_models]
        
        # Step 2: Filter by date range if provided
        if start_date or end_date:
            tickets = self._filter_by_date_range(tickets, start_date, end_date)
        
        # Step 3: Enrich each ticket with billing information
        enriched_tickets = []
        for ticket in tickets:
            enriched_ticket = self._enrich_ticket_with_billing(ticket)
            enriched_tickets.append(enriched_ticket)
            
            # Update ticket in database with billing info
            self.ticket_repo.update_billing_info(
                ticket_id=enriched_ticket.ticket_id,
                clause_id=enriched_ticket.clause_id,
                billable_amount=float(enriched_ticket.billable_amount),
                is_billable=enriched_ticket.is_billable
            )
        
        return enriched_tickets
    
    def _convert_ticket_model(self, ticket_model) -> JiraTicket:
        """Convert SQLAlchemy model to Pydantic model"""
        # Convert labels from comma-separated string to list
        labels = [l.strip() for l in ticket_model.labels.split(',')] if ticket_model.labels else []
        
        return JiraTicket(
            ticket_id=ticket_model.ticket_id,
            summary=ticket_model.summary,
            description=ticket_model.description,
            status=TicketStatus(ticket_model.status.value),
            hours_worked=ticket_model.hours_worked,
            labels=labels,
            assignee=ticket_model.assignee,
            resolved_at=ticket_model.resolved_at,
            clause_id=ticket_model.clause_id,
            billable_amount=ticket_model.billable_amount,
            is_billable=ticket_model.is_billable
        )
    
    def _normalize_datetime(self, dt: Optional[datetime]) -> Optional[datetime]:
        """
        Normalize datetime to be timezone-aware (UTC)
        If datetime is naive, assume it's UTC
        """
        if dt is None:
            return None
        
        if dt.tzinfo is None:
            # Naive datetime - assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Already timezone-aware - convert to UTC
            return dt.astimezone(timezone.utc)
    
    def _filter_by_date_range(
        self,
        tickets: List[JiraTicket],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[JiraTicket]:
        """Filter tickets by date range"""
        filtered = tickets
        
        # Normalize input dates to UTC
        start_date_utc = self._normalize_datetime(start_date)
        end_date_utc = self._normalize_datetime(end_date)
        
        if start_date_utc:
            filtered = [
                t for t in filtered
                if t.resolved_at and self._normalize_datetime(t.resolved_at) >= start_date_utc
            ]
        
        if end_date_utc:
            filtered = [
                t for t in filtered
                if t.resolved_at and self._normalize_datetime(t.resolved_at) <= end_date_utc
            ]
        
        return filtered
    
    def _enrich_ticket_with_billing(self, ticket: JiraTicket) -> JiraTicket:
        """
        Enrich a single ticket with billing information
        This modifies the ticket object in place
        """
        # Match ticket to clause using MappingEngine with db session
        clause_model = MappingEngine.match_ticket_to_clause(ticket, self.db)
        
        if clause_model:
            # Calculate billable amount
            billable_amount = MappingEngine.calculate_line_cost(ticket, clause_model)
            
            # Update ticket with billing info
            ticket.clause_id = clause_model.clause_id
            ticket.billable_amount = billable_amount
            ticket.is_billable = True
            
            print(f"Enriched Ticket {ticket.ticket_id}: Clause={clause_model.clause_id}, Amount={billable_amount}")
        else:
            # No matching clause found
            ticket.clause_id = None
            ticket.billable_amount = Decimal("0.00")
            ticket.is_billable = False
            
            print(f"Ticket {ticket.ticket_id}: No matching clause found")
        
        return ticket
    
    async def authenticate(self) -> bool:
        """Validate Jira token"""
        # In production, make a test API call to validate token
        return bool(self.user_token)