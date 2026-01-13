from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from .base import BaseRepository
from ..models import JiraTicketModel, TicketStatusEnum


class TicketRepository(BaseRepository[JiraTicketModel]):
    """Repository for Jira Ticket operations"""
    
    def __init__(self, db: Session):
        super().__init__(JiraTicketModel, db)
    
    def get_by_status(self, status: TicketStatusEnum) -> List[JiraTicketModel]:
        """Get all tickets with a specific status"""
        return self.db.query(JiraTicketModel).filter(
            JiraTicketModel.status == status
        ).all()
    
    def get_billable_tickets(self) -> List[JiraTicketModel]:
        """Get all billable tickets"""
        return self.db.query(JiraTicketModel).filter(
            JiraTicketModel.is_billable == True
        ).all()
    
    def get_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[JiraTicketModel]:
        """Get tickets resolved within a date range"""
        query = self.db.query(JiraTicketModel).filter(
            JiraTicketModel.resolved_at.isnot(None)
        )
        
        if start_date:
            query = query.filter(JiraTicketModel.resolved_at >= start_date)
        
        if end_date:
            query = query.filter(JiraTicketModel.resolved_at <= end_date)
        
        return query.all()
    
    def get_by_label(self, label: str) -> List[JiraTicketModel]:
        """Get tickets with a specific label"""
        return self.db.query(JiraTicketModel).filter(
            JiraTicketModel.labels.like(f"%{label}%")
        ).all()
    
    def get_by_assignee(self, assignee: str) -> List[JiraTicketModel]:
        """Get tickets assigned to a specific user"""
        return self.db.query(JiraTicketModel).filter(
            JiraTicketModel.assignee == assignee
        ).all()
    
    def get_by_clause(self, clause_id: str) -> List[JiraTicketModel]:
        """Get all tickets mapped to a specific clause"""
        return self.db.query(JiraTicketModel).filter(
            JiraTicketModel.clause_id == clause_id
        ).all()
    
    def update_billing_info(
        self,
        ticket_id: str,
        clause_id: Optional[str],
        billable_amount: float,
        is_billable: bool
    ) -> Optional[JiraTicketModel]:
        """Update ticket's billing information"""
        try:
            ticket = self.get(ticket_id)
            if ticket:
                ticket.clause_id = clause_id
                ticket.billable_amount = billable_amount
                ticket.is_billable = is_billable
                self.db.commit()
                self.db.refresh(ticket)
            return ticket
        except Exception as e:
            self.db.rollback()
            raise e
    
    def bulk_create(self, tickets_data: List[dict]) -> List[JiraTicketModel]:
        """Bulk create or update tickets"""
        try:
            created_tickets = []
            for ticket_data in tickets_data:
                # Check if ticket exists
                existing = self.get(ticket_data['ticket_id'])
                if existing:
                    # Update existing
                    for key, value in ticket_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    created_tickets.append(existing)
                else:
                    # Create new
                    new_ticket = JiraTicketModel(**ticket_data)
                    self.db.add(new_ticket)
                    created_tickets.append(new_ticket)
            
            self.db.commit()
            return created_tickets
        except Exception as e:
            self.db.rollback()
            raise e