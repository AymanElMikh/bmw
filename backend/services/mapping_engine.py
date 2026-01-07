from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

from models import JiraTicket, TicketStatus
from database import ClauseRepository
from database.models import LegalClauseModel


class MappingEngine:
    """Service for mapping Jira tickets to legal clauses"""
    
    @staticmethod
    def match_ticket_to_clause(ticket: JiraTicket, db: Session) -> Optional[LegalClauseModel]:
        """
        Match a Jira ticket to a legal clause based on labels
        Returns the first matching active clause or None
        """
        if not ticket.labels:
            return None
        
        clause_repo = ClauseRepository(db)
        
        # Try to find a matching clause for any label
        for label in ticket.labels:
            clause = clause_repo.get_by_label(label)
            if clause and clause.is_active:
                return clause
        
        return None
    
    @staticmethod
    def calculate_line_cost(ticket: JiraTicket, clause: LegalClauseModel) -> Decimal:
        """Calculate the cost for a ticket based on hours and clause price"""
        if not ticket.hours_worked or not clause.unit_price:
            return Decimal("0.00")
        
        cost = ticket.hours_worked * clause.unit_price
        return round(cost, 2)
    
    @staticmethod
    def validate_mapping(ticket: JiraTicket, db: Session) -> Tuple[bool, str]:
        """
        Validate if a ticket can be mapped and billed
        Returns (is_valid, error_message)
        """
        if ticket.status != TicketStatus.CLOSED:
            return False, f"Ticket {ticket.ticket_id} is not closed"
        
        if not ticket.labels:
            return False, f"Ticket {ticket.ticket_id} has no labels"
        
        if not ticket.hours_worked or ticket.hours_worked <= 0:
            return False, f"Ticket {ticket.ticket_id} has no hours logged"
        
        # Check if any label matches a clause
        clause = MappingEngine.match_ticket_to_clause(ticket, db)
        if not clause:
            return False, f"Ticket {ticket.ticket_id} has no matching legal clause"
        
        return True, ""
    
    @staticmethod
    def process_tickets_batch(tickets: List[JiraTicket], db: Session) -> Dict:
        """
        Process multiple tickets and return mapping results
        Assumes tickets are already enriched with billing info
        """
        clause_repo = ClauseRepository(db)
        
        results = {
            "valid": [],
            "invalid": [],
            "total_cost": Decimal("0.00"),
            "total_hours": Decimal("0.00")
        }
        
        for ticket in tickets:
            is_valid, error = MappingEngine.validate_mapping(ticket, db)
            
            if is_valid and ticket.is_billable:
                clause = clause_repo.get(ticket.clause_id)
                results["valid"].append({
                    "ticket": ticket,
                    "clause": clause,
                    "cost": ticket.billable_amount
                })
                results["total_cost"] += ticket.billable_amount
                results["total_hours"] += ticket.hours_worked
            else:
                results["invalid"].append({
                    "ticket": ticket,
                    "error": error if error else "Not billable"
                })
        
        return results