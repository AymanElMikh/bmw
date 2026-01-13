from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from decimal import Decimal

from .base import BaseRepository
from ..models import InvoiceModel, InvoiceLineModel, InvoiceStatusEnum


class InvoiceRepository(BaseRepository[InvoiceModel]):
    """Repository for Invoice operations"""
    
    def __init__(self, db: Session):
        super().__init__(InvoiceModel, db)
    
    def get_with_lines(self, invoice_id: str) -> Optional[InvoiceModel]:
        """Get invoice with all line items loaded"""
        return self.db.query(InvoiceModel).options(
            joinedload(InvoiceModel.lines)
        ).filter(InvoiceModel.invoice_id == invoice_id).first()
    
    def get_by_creator(self, user_id: str) -> List[InvoiceModel]:
        """Get all invoices created by a specific user"""
        return self.db.query(InvoiceModel).filter(
            InvoiceModel.created_by == user_id
        ).all()
    
    def get_by_status(self, status: InvoiceStatusEnum) -> List[InvoiceModel]:
        """Get all invoices with a specific status"""
        return self.db.query(InvoiceModel).filter(
            InvoiceModel.status == status
        ).all()
    
    def get_by_billing_period(self, billing_period: str) -> List[InvoiceModel]:
        """Get all invoices for a specific billing period"""
        return self.db.query(InvoiceModel).filter(
            InvoiceModel.billing_period == billing_period
        ).all()
    
    def get_by_project(self, project_name: str) -> List[InvoiceModel]:
        """Get all invoices for a specific project"""
        return self.db.query(InvoiceModel).filter(
            InvoiceModel.project_name == project_name
        ).all()
    
    def create_with_lines(
        self,
        invoice_data: Dict,
        lines_data: List[Dict]
    ) -> InvoiceModel:
        """Create an invoice with its line items"""
        try:
            # Create invoice
            invoice = InvoiceModel(**invoice_data)
            self.db.add(invoice)
            self.db.flush()  # Get the invoice_id
            
            # Create line items
            for line_data in lines_data:
                line = InvoiceLineModel(
                    invoice_id=invoice.invoice_id,
                    **line_data
                )
                self.db.add(line)
            
            self.db.commit()
            self.db.refresh(invoice)
            
            # Load lines relationship
            return self.get_with_lines(invoice.invoice_id)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_status(
        self,
        invoice_id: str,
        new_status: InvoiceStatusEnum
    ) -> Optional[InvoiceModel]:
        """Update invoice status"""
        try:
            invoice = self.get(invoice_id)
            if invoice:
                invoice.status = new_status
                self.db.commit()
                self.db.refresh(invoice)
            return invoice
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_total_by_period(self, billing_period: str) -> Decimal:
        """Get total invoiced amount for a billing period"""
        from sqlalchemy import func
        
        result = self.db.query(
            func.sum(InvoiceModel.total_amount)
        ).filter(
            InvoiceModel.billing_period == billing_period
        ).scalar()
        
        return result or Decimal("0.00")
    
    def get_statistics(self, user_id: Optional[str] = None) -> Dict:
        """Get invoice statistics"""
        from sqlalchemy import func
        
        query = self.db.query(
            func.count(InvoiceModel.invoice_id).label('total_count'),
            func.sum(InvoiceModel.total_amount).label('total_amount'),
            InvoiceModel.status
        )
        
        if user_id:
            query = query.filter(InvoiceModel.created_by == user_id)
        
        query = query.group_by(InvoiceModel.status)
        
        results = query.all()
        
        stats = {
            'total_invoices': 0,
            'total_amount': Decimal("0.00"),
            'by_status': {}
        }
        
        for count, amount, status in results:
            stats['total_invoices'] += count
            stats['total_amount'] += (amount or Decimal("0.00"))
            stats['by_status'][status.value] = {
                'count': count,
                'amount': float(amount or Decimal("0.00"))
            }
        
        return stats


class InvoiceLineRepository(BaseRepository[InvoiceLineModel]):
    """Repository for Invoice Line operations"""
    
    def __init__(self, db: Session):
        super().__init__(InvoiceLineModel, db)
    
    def get_by_invoice(self, invoice_id: str) -> List[InvoiceLineModel]:
        """Get all lines for a specific invoice"""
        return self.db.query(InvoiceLineModel).filter(
            InvoiceLineModel.invoice_id == invoice_id
        ).all()
    
    def get_by_ticket(self, ticket_id: str) -> List[InvoiceLineModel]:
        """Get all invoice lines for a specific ticket"""
        return self.db.query(InvoiceLineModel).filter(
            InvoiceLineModel.jira_ticket_id == ticket_id
        ).all()
    
    def get_by_clause(self, clause_id: str) -> List[InvoiceLineModel]:
        """Get all invoice lines for a specific clause"""
        return self.db.query(InvoiceLineModel).filter(
            InvoiceLineModel.clause_id == clause_id
        ).all()