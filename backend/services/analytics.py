from typing import Optional, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

from database import InvoiceRepository, ClauseRepository


class AnalyticsService:
    """Service for generating reports and analytics"""
    
    @staticmethod
    def get_monthly_summary(billing_period: str, db: Session, user_id: Optional[str] = None) -> Dict:
        """Generate monthly billing summary"""
        invoice_repo = InvoiceRepository(db)
        clause_repo = ClauseRepository(db)
        
        # Get invoices for the period
        if user_id:
            all_invoices = invoice_repo.get_by_creator(user_id)
        else:
            all_invoices = invoice_repo.get_all()
        
        # Filter by billing period
        period_invoices = [
            inv for inv in all_invoices
            if inv.billing_period == billing_period
        ]
        
        total_amount = sum(inv.total_amount for inv in period_invoices)
        
        total_hours = Decimal("0.00")
        total_tickets = 0
        
        for invoice in period_invoices:
            for line in invoice.lines:
                total_hours += line.hours_worked
                total_tickets += 1
        
        # Breakdown by clause
        clause_breakdown = {}
        for invoice in period_invoices:
            for line in invoice.lines:
                clause_id = line.clause_id
                
                if clause_id not in clause_breakdown:
                    clause = clause_repo.get(clause_id)
                    clause_breakdown[clause_id] = {
                        "clause_name": clause.clause_name if clause else clause_id,
                        "hours": Decimal("0.00"),
                        "amount": Decimal("0.00"),
                        "tickets": 0
                    }
                
                clause_breakdown[clause_id]["hours"] += line.hours_worked
                clause_breakdown[clause_id]["amount"] += line.line_total
                clause_breakdown[clause_id]["tickets"] += 1
        
        return {
            "billing_period": billing_period,
            "total_hours": float(total_hours),
            "total_amount": float(total_amount),
            "tickets_billed": total_tickets,
            "invoices_count": len(period_invoices),
            "breakdown_by_clause": clause_breakdown
        }
    
    @staticmethod
    def get_user_performance(user_id: str, db: Session, months: int = 3) -> Dict:
        """Get performance metrics for a user"""
        invoice_repo = InvoiceRepository(db)
        
        # Get all invoices for user
        invoices = invoice_repo.get_by_creator(user_id)
        
        # Calculate metrics
        total_invoices = len(invoices)
        total_revenue = sum(inv.total_amount for inv in invoices)
        
        # Status breakdown
        status_count = {}
        for invoice in invoices:
            status = invoice.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            "user_id": user_id,
            "total_invoices": total_invoices,
            "total_revenue": float(total_revenue),
            "status_breakdown": status_count,
            "avg_invoice_amount": float(total_revenue / total_invoices) if total_invoices > 0 else 0
        }
    
    @staticmethod
    def get_invoice_statistics(db: Session, user_id: Optional[str] = None) -> Dict:
        """Get comprehensive invoice statistics"""
        invoice_repo = InvoiceRepository(db)
        return invoice_repo.get_statistics(user_id)
    
    @staticmethod
    def get_clause_utilization(db: Session, billing_period: Optional[str] = None) -> Dict:
        """Get clause utilization statistics"""
        invoice_repo = InvoiceRepository(db)
        clause_repo = ClauseRepository(db)
        
        # Get all active clauses
        active_clauses = clause_repo.get_active_clauses()
        
        # Get invoices
        if billing_period:
            invoices = invoice_repo.get_by_billing_period(billing_period)
        else:
            invoices = invoice_repo.get_all()
        
        # Calculate utilization
        clause_usage = {}
        for clause in active_clauses:
            clause_usage[clause.clause_id] = {
                "clause_name": clause.clause_name,
                "unit_price": float(clause.unit_price),
                "total_hours": 0.0,
                "total_amount": 0.0,
                "ticket_count": 0
            }
        
        # Aggregate from invoices
        for invoice in invoices:
            for line in invoice.lines:
                if line.clause_id in clause_usage:
                    clause_usage[line.clause_id]["total_hours"] += float(line.hours_worked)
                    clause_usage[line.clause_id]["total_amount"] += float(line.line_total)
                    clause_usage[line.clause_id]["ticket_count"] += 1
        
        return {
            "period": billing_period or "all_time",
            "total_clauses": len(active_clauses),
            "clauses_used": len([c for c in clause_usage.values() if c["ticket_count"] > 0]),
            "clause_details": clause_usage
        }