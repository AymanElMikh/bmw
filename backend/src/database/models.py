from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .config import Base


# Enums - Aligned with Pydantic models
class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    VIEWER = "VIEWER"


class TicketStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class InvoiceStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class CurrencyEnum(str, enum.Enum):
    EUR = "EUR"
    USD = "USD"


# Database Models
class UserModel(Base):
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRoleEnum), nullable=False, default=UserRoleEnum.VIEWER)
    has_jira_token = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = relationship("InvoiceModel", back_populates="creator")
    audit_logs = relationship("AuditLogModel", back_populates="user")


class UserTokenModel(Base):
    __tablename__ = "user_tokens"
    
    user_id = Column(String(50), ForeignKey("users.user_id"), primary_key=True)
    encrypted_token = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LegalClauseModel(Base):
    __tablename__ = "legal_clauses"
    
    clause_id = Column(String(50), primary_key=True, index=True)
    clause_name = Column(String(200), nullable=False)
    description = Column(Text)
    unit_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(SQLEnum(CurrencyEnum), nullable=False, default=CurrencyEnum.EUR)
    effective_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    created_by = Column(String(50), ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    invoice_lines = relationship("InvoiceLineModel", back_populates="clause")


class JiraTicketModel(Base):
    __tablename__ = "jira_tickets"
    
    ticket_id = Column(String(50), primary_key=True, index=True)
    summary = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TicketStatusEnum), nullable=False)
    hours_worked = Column(Numeric(10, 2), default=0)
    labels = Column(Text)  # Stored as comma-separated values
    assignee = Column(String(100))
    resolved_at = Column(DateTime, nullable=True)
    clause_id = Column(String(50), ForeignKey("legal_clauses.clause_id"), nullable=True)
    billable_amount = Column(Numeric(10, 2), default=0)
    is_billable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvoiceModel(Base):
    __tablename__ = "invoices"
    
    invoice_id = Column(String(50), primary_key=True, index=True)
    project_name = Column(String(200), nullable=False)
    billing_period = Column(String(20), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(SQLEnum(CurrencyEnum), nullable=False, default=CurrencyEnum.EUR)
    status = Column(SQLEnum(InvoiceStatusEnum), nullable=False, default=InvoiceStatusEnum.DRAFT)
    created_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("UserModel", back_populates="invoices")
    lines = relationship("InvoiceLineModel", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineModel(Base):
    __tablename__ = "invoice_lines"
    
    line_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(50), ForeignKey("invoices.invoice_id"), nullable=False)
    jira_ticket_id = Column(String(50), nullable=False, index=True)
    clause_id = Column(String(50), ForeignKey("legal_clauses.clause_id"), nullable=False)
    hours_worked = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    invoice = relationship("InvoiceModel", back_populates="lines")
    clause = relationship("LegalClauseModel", back_populates="invoice_lines")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="audit_logs")