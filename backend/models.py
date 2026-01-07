from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    VIEWER = "VIEWER"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"


class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"


# ============================================================================
# USER MODELS
# ============================================================================

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    jira_token: str = Field(..., min_length=10)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    jira_token: Optional[str] = None


class User(UserBase):
    user_id: str
    created_at: datetime
    has_jira_token: bool

    class Config:
        from_attributes = True


class UserWithToken(User):
    jira_token_encrypted: str


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class JiraTokenRequest(BaseModel):
    token: str = Field(..., min_length=10)


# ============================================================================
# LEGAL CLAUSE MODELS
# ============================================================================

class LegalClauseBase(BaseModel):
    clause_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    unit_price: Decimal = Field(..., gt=0)
    currency: Currency
    effective_date: datetime

    @field_validator('unit_price')
    @classmethod
    def round_unit_price(cls, v):
        return round(v, 2)


class LegalClauseCreate(LegalClauseBase):
    clause_id: str = Field(..., pattern=r"^[A-Z_0-9]+$", max_length=50)


class LegalClauseUpdate(BaseModel):
    clause_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[Currency] = None
    effective_date: Optional[datetime] = None

    @field_validator('unit_price')
    @classmethod
    def round_unit_price(cls, v):
        if v is not None:
            return round(v, 2)
        return v


class LegalClause(LegalClauseBase):
    clause_id: str
    created_by: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# JIRA TICKET MODELS
# ============================================================================

class JiraTicketBase(BaseModel):
    ticket_id: str = Field(..., pattern=r"^[A-Z]+-\d+$")
    summary: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: TicketStatus
    hours_worked: Decimal = Field(..., ge=0)
    labels: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    resolved_at: Optional[datetime] = None

    @field_validator('hours_worked')
    @classmethod
    def round_hours(cls, v):
        return round(v, 2)


class JiraTicket(JiraTicketBase):
    clause_id: Optional[str] = None
    is_billable: bool = False
    billable_amount: Optional[Decimal] = None

    @field_validator('is_billable')
    @classmethod
    def check_billable(cls, v, info):
        values = info.data
        return values.get('status') == TicketStatus.CLOSED and bool(values.get('labels'))


class JiraFetchRequest(BaseModel):
    project_key: str = Field(..., pattern=r"^[A-Z]+$")
    billing_period_start: datetime
    billing_period_end: datetime
    status_filter: Optional[TicketStatus] = TicketStatus.CLOSED
    label_filter: Optional[str] = None


class JiraFetchResponse(BaseModel):
    tickets: List[JiraTicket]
    total_count: int
    billable_count: int
    excluded_count: int
    excluded_tickets: List[str] = Field(default_factory=list)


# ============================================================================
# INVOICE LINE MODELS
# ============================================================================

class InvoiceLineBase(BaseModel):
    jira_ticket_id: str
    clause_id: str
    hours_worked: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., gt=0)

    @field_validator('hours_worked', 'unit_price')
    @classmethod
    def round_decimals(cls, v):
        return round(v, 2)


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLine(InvoiceLineBase):
    line_id: int
    invoice_id: str
    line_total: Decimal

    @field_validator('line_total', mode='before')
    @classmethod
    def calculate_total(cls, v, info):
        values = info.data
        if v is None and 'hours_worked' in values and 'unit_price' in values:
            return round(values['hours_worked'] * values['unit_price'], 2)
        return round(v, 2) if v is not None else v

    class Config:
        from_attributes = True


# ============================================================================
# INVOICE MODELS
# ============================================================================

class InvoiceBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    billing_period: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class InvoiceCreate(InvoiceBase):
    ticket_ids: List[str] = Field(..., min_items=1)


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None


class Invoice(InvoiceBase):
    invoice_id: str
    total_amount: Decimal
    status: InvoiceStatus
    created_by: str
    created_at: datetime
    lines: List[InvoiceLine] = Field(default_factory=list)
    currency: Currency = Currency.EUR

    @field_validator('total_amount', mode='before')
    @classmethod
    def calculate_total_amount(cls, v, info):
        values = info.data
        if v is None and 'lines' in values:
            return sum(line.line_total for line in values['lines'])
        return round(v, 2) if v is not None else v

    class Config:
        from_attributes = True


class InvoiceListItem(BaseModel):
    invoice_id: str
    project_name: str
    billing_period: str
    total_amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    line_count: int


class InvoiceGenerateRequest(BaseModel):
    project_name: str
    billing_period: str
    jira_project_key: str
    billing_period_start: datetime
    billing_period_end: datetime


# ============================================================================
# AUDIT LOG MODELS
# ============================================================================

class AuditLogBase(BaseModel):
    action: str = Field(..., max_length=100)
    details: Optional[str] = Field(None, max_length=2000)


class AuditLogCreate(AuditLogBase):
    user_id: str


class AuditLog(AuditLogBase):
    log_id: int
    user_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ============================================================================
# REPORT MODELS
# ============================================================================

class MonthlySummary(BaseModel):
    billing_period: str
    total_hours: Decimal
    total_amount: Decimal
    tickets_billed: int
    invoices_count: int
    breakdown_by_clause: dict


class ExportFormat(str, Enum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    SAP_XML = "SAP_XML"


class ExportRequest(BaseModel):
    invoice_id: str
    format: ExportFormat


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None