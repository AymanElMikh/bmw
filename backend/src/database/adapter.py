"""
Database Adapter - Maintains backward compatibility with existing code
Wraps repository pattern with the old MockDatabase interface
"""

from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from .config import SessionLocal
from .repositories import (
    UserRepository,
    ClauseRepository,
    TicketRepository,
    InvoiceRepository,
    InvoiceLineRepository,
    AuditRepository
)
from models import (
    User, LegalClause, JiraTicket, Invoice, InvoiceLine, AuditLog,
    TicketStatus, InvoiceStatus, Currency
)


class DatabaseAdapter:
    """
    Adapter to maintain compatibility with existing code
    Converts between Pydantic models and SQLAlchemy models
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.user_repo = UserRepository(self.db)
        self.clause_repo = ClauseRepository(self.db)
        self.ticket_repo = TicketRepository(self.db)
        self.invoice_repo = InvoiceRepository(self.db)
        self.invoice_line_repo = InvoiceLineRepository(self.db)
        self.audit_repo = AuditRepository(self.db)
    
    def _convert_user(self, user_model) -> Optional[User]:
        """Convert SQLAlchemy UserModel to Pydantic User"""
        if not user_model:
            return None
        return User(
            user_id=user_model.user_id,
            name=user_model.name,
            email=user_model.email,
            role=user_model.role.value,
            has_jira_token=user_model.has_jira_token,
            created_at=user_model.created_at
        )
    
    def _convert_clause(self, clause_model) -> Optional[LegalClause]:
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
    
    def _convert_ticket(self, ticket_model) -> Optional[JiraTicket]:
        """Convert SQLAlchemy JiraTicketModel to Pydantic JiraTicket"""
        if not ticket_model:
            return None
        
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
    
    def _convert_invoice_line(self, line_model) -> Optional[InvoiceLine]:
        """Convert SQLAlchemy InvoiceLineModel to Pydantic InvoiceLine"""
        if not line_model:
            return None
        return InvoiceLine(
            line_id=line_model.line_id,
            invoice_id=line_model.invoice_id,
            jira_ticket_id=line_model.jira_ticket_id,
            clause_id=line_model.clause_id,
            hours_worked=line_model.hours_worked,
            unit_price=line_model.unit_price,
            line_total=line_model.line_total
        )
    
    def _convert_invoice(self, invoice_model) -> Optional[Invoice]:
        """Convert SQLAlchemy InvoiceModel to Pydantic Invoice"""
        if not invoice_model:
            return None
        
        lines = [self._convert_invoice_line(line) for line in invoice_model.lines]
        
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
    
    def _convert_audit_log(self, log_model) -> Optional[AuditLog]:
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
    
    # ========================================================================
    # USER OPERATIONS
    # ========================================================================
    
    def get_user(self, user_id: str) -> Optional[User]:
        user_model = self.user_repo.get(user_id)
        return self._convert_user(user_model)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        user_model = self.user_repo.get_by_email(email)
        return self._convert_user(user_model)
    
    def create_user(self, user_data: dict) -> User:
        user_model = self.user_repo.create(user_data)
        return self._convert_user(user_model)
    
    def update_user_token(self, user_id: str, token: str) -> bool:
        return self.user_repo.update_jira_token(user_id, f"encrypted_{token}")
    
    def list_users(self) -> List[User]:
        user_models = self.user_repo.get_all()
        return [self._convert_user(u) for u in user_models]
    
    # ========================================================================
    # LEGAL CLAUSE OPERATIONS
    # ========================================================================
    
    def get_clause(self, clause_id: str) -> Optional[LegalClause]:
        clause_model = self.clause_repo.get(clause_id)
        return self._convert_clause(clause_model)
    
    def create_clause(self, clause_data: dict, created_by: str) -> LegalClause:
        clause_data['created_by'] = created_by
        clause_model = self.clause_repo.create(clause_data)
        return self._convert_clause(clause_model)
    
    def update_clause(self, clause_id: str, updates: dict) -> Optional[LegalClause]:
        clause_model = self.clause_repo.update(clause_id, updates)
        return self._convert_clause(clause_model)
    
    def list_clauses(self, active_only: bool = True) -> List[LegalClause]:
        if active_only:
            clause_models = self.clause_repo.get_active_clauses()
        else:
            clause_models = self.clause_repo.get_all()
        return [self._convert_clause(c) for c in clause_models]
    
    # ========================================================================
    # JIRA OPERATIONS
    # ========================================================================
    
    def get_jira_tickets(
        self,
        status: Optional[TicketStatus] = None,
        label: Optional[str] = None
    ) -> List[JiraTicket]:
        if status:
            from .models import TicketStatusEnum
            status_enum = TicketStatusEnum(status.value)
            ticket_models = self.ticket_repo.get_by_status(status_enum)
        elif label:
            ticket_models = self.ticket_repo.get_by_label(label)
        else:
            ticket_models = self.ticket_repo.get_all()
        
        return [self._convert_ticket(t) for t in ticket_models]
    
    # ========================================================================
    # INVOICE OPERATIONS
    # ========================================================================
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        invoice_model = self.invoice_repo.get_with_lines(invoice_id)
        return self._convert_invoice(invoice_model)
    
    def create_invoice(
        self,
        invoice_data: dict,
        lines: List[dict],
        created_by: str
    ) -> Invoice:
        from .models import InvoiceStatusEnum, CurrencyEnum
        import uuid
        
        # Generate invoice ID
        invoice_id = f"INV-{datetime.now().strftime('%Y-%m')}-{str(uuid.uuid4())[:3].upper()}"
        
        # Prepare invoice data
        full_invoice_data = {
            "invoice_id": invoice_id,
            "created_by": created_by,
            "status": InvoiceStatusEnum.DRAFT,
            **invoice_data
        }
        
        # Convert Currency enum if needed
        if 'currency' in full_invoice_data:
            if isinstance(full_invoice_data['currency'], Currency):
                full_invoice_data['currency'] = CurrencyEnum(full_invoice_data['currency'].value)
        
        # Create invoice with lines
        invoice_model = self.invoice_repo.create_with_lines(full_invoice_data, lines)
        return self._convert_invoice(invoice_model)
    
    def update_invoice(self, invoice_id: str, updates: dict) -> Optional[Invoice]:
        from .models import InvoiceStatusEnum
        
        # Convert status if needed
        if 'status' in updates and isinstance(updates['status'], InvoiceStatus):
            updates['status'] = InvoiceStatusEnum(updates['status'].value)
        
        invoice_model = self.invoice_repo.update(invoice_id, updates)
        return self._convert_invoice(invoice_model)
    
    def list_invoices(self, created_by: Optional[str] = None) -> List[Invoice]:
        if created_by:
            invoice_models = self.invoice_repo.get_by_creator(created_by)
        else:
            invoice_models = self.invoice_repo.get_all()
        
        return [self._convert_invoice(i) for i in invoice_models]
    
    # ========================================================================
    # AUDIT LOG OPERATIONS
    # ========================================================================
    
    def create_audit_log(
        self,
        user_id: str,
        action: str,
        details: Optional[str] = None
    ) -> AuditLog:
        log_model = self.audit_repo.log_action(user_id, action, details)
        return self._convert_audit_log(log_model)
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        if user_id:
            log_models = self.audit_repo.get_by_user(user_id)
        elif action:
            log_models = self.audit_repo.get_by_action(action)
        else:
            log_models = self.audit_repo.get_recent()
        
        return [self._convert_audit_log(l) for l in log_models]


# Global instance for backward compatibility
db = DatabaseAdapter()