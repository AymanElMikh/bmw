"""
Model Converters
Convert between SQLAlchemy models and Pydantic models
"""
from sqlalchemy.orm import Session
from src.models import (
    User, UserRole,
    LegalClause, Currency,
    Invoice, InvoiceLine, InvoiceStatus,
    AuditLog
)


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