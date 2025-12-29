from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from models import (
    User, UserRole, LegalClause, JiraTicket, Invoice, InvoiceLine,
    AuditLog, TicketStatus, InvoiceStatus, Currency
)


# ============================================================================
# MOCK DATABASE
# ============================================================================

class MockDatabase:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.user_tokens: Dict[str, str] = {}  # user_id -> encrypted_token
        self.legal_clauses: Dict[str, LegalClause] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.invoice_lines: List[InvoiceLine] = []
        self.audit_logs: List[AuditLog] = []
        self.jira_tickets: List[JiraTicket] = []  # Mock Jira data
        
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with sample data"""
        # Create mock users
        self.users = {
            "user_001": User(
                user_id="user_001",
                name="John Doe",
                email="john.doe@altran.com",
                role=UserRole.PROJECT_LEADER,
                created_at=datetime.now() - timedelta(days=30),
                has_jira_token=True
            ),
            "user_002": User(
                user_id="user_002",
                name="Jane Smith",
                email="jane.smith@altran.com",
                role=UserRole.ADMIN,
                created_at=datetime.now() - timedelta(days=60),
                has_jira_token=True
            ),
            "user_003": User(
                user_id="user_003",
                name="Bob Wilson",
                email="bob.wilson@altran.com",
                role=UserRole.VIEWER,
                created_at=datetime.now() - timedelta(days=15),
                has_jira_token=False
            )
        }
        
        # Mock encrypted tokens
        self.user_tokens = {
            "user_001": "encrypted_token_abc123",
            "user_002": "encrypted_token_xyz789"
        }
        
        # Create mock legal clauses
        self.legal_clauses = {
            "FLASH_001": LegalClause(
                clause_id="FLASH_001",
                clause_name="Standard Development",
                description="Regular software development work",
                unit_price=Decimal("85.00"),
                currency=Currency.EUR,
                effective_date=datetime(2024, 1, 1),
                created_by="user_002",
                created_at=datetime(2024, 1, 1),
                is_active=True
            ),
            "FLASH_002": LegalClause(
                clause_id="FLASH_002",
                clause_name="Bug Fixing",
                description="Critical bug resolution",
                unit_price=Decimal("95.00"),
                currency=Currency.EUR,
                effective_date=datetime(2024, 1, 1),
                created_by="user_002",
                created_at=datetime(2024, 1, 1),
                is_active=True
            ),
            "FLASH_003": LegalClause(
                clause_id="FLASH_003",
                clause_name="Code Review",
                description="Peer code review and quality assurance",
                unit_price=Decimal("75.00"),
                currency=Currency.EUR,
                effective_date=datetime(2024, 1, 1),
                created_by="user_002",
                created_at=datetime(2024, 1, 1),
                is_active=True
            ),
            "FLASH_004": LegalClause(
                clause_id="FLASH_004",
                clause_name="Technical Documentation",
                description="Technical writing and documentation",
                unit_price=Decimal("70.00"),
                currency=Currency.EUR,
                effective_date=datetime(2024, 1, 1),
                created_by="user_002",
                created_at=datetime(2024, 1, 1),
                is_active=True
            )
        }
        
        # Create mock Jira tickets
        self.jira_tickets = [
            JiraTicket(
                ticket_id="BMW-101",
                summary="Implement user authentication module",
                description="Add OAuth2 authentication",
                status=TicketStatus.CLOSED,
                hours_worked=Decimal("16.5"),
                labels=["FLASH_001"],
                assignee="john.doe@altran.com",
                clause_id="FLASH_001",
                is_billable=True
            ),
            JiraTicket(
                ticket_id="BMW-102",
                summary="Fix payment gateway bug",
                description="Critical issue with payment processing",
                status=TicketStatus.CLOSED,
                hours_worked=Decimal("8.0"),
                labels=["FLASH_002"],
                assignee="john.doe@altran.com",
                clause_id="FLASH_002",
                is_billable=True
            ),
            JiraTicket(
                ticket_id="BMW-103",
                summary="Code review for PR #234",
                description="Review authentication changes",
                status=TicketStatus.CLOSED,
                hours_worked=Decimal("4.0"),
                labels=["FLASH_003"],
                assignee="jane.smith@altran.com",
                clause_id="FLASH_003",
                is_billable=True
            ),
            JiraTicket(
                ticket_id="BMW-104",
                summary="Update API documentation",
                description="Document new endpoints",
                status=TicketStatus.CLOSED,
                hours_worked=Decimal("6.5"),
                labels=["FLASH_004"],
                assignee="john.doe@altran.com",
                clause_id="FLASH_004",
                is_billable=True
            ),
            JiraTicket(
                ticket_id="BMW-105",
                summary="Refactor database queries",
                description="Optimize slow queries",
                status=TicketStatus.IN_PROGRESS,
                hours_worked=Decimal("12.0"),
                labels=["FLASH_001"],
                assignee="john.doe@altran.com",
                clause_id="FLASH_001",
                is_billable=False
            ),
            JiraTicket(
                ticket_id="BMW-106",
                summary="Internal research task",
                description="Research new framework",
                status=TicketStatus.CLOSED,
                hours_worked=Decimal("8.0"),
                labels=[],  # No billable label
                assignee="bob.wilson@altran.com",
                clause_id=None,
                is_billable=False
            ),
        ]
        
        # Create a sample invoice
        invoice_id = "INV-2024-12-001"
        
        # Calculate line totals
        line_data = [
            {
                "line_id": 1,
                "invoice_id": invoice_id,
                "jira_ticket_id": "BMW-101",
                "clause_id": "FLASH_001",
                "hours_worked": Decimal("16.5"),
                "unit_price": Decimal("85.00")
            },
            {
                "line_id": 2,
                "invoice_id": invoice_id,
                "jira_ticket_id": "BMW-102",
                "clause_id": "FLASH_002",
                "hours_worked": Decimal("8.0"),
                "unit_price": Decimal("95.00")
            },
            {
                "line_id": 3,
                "invoice_id": invoice_id,
                "jira_ticket_id": "BMW-103",
                "clause_id": "FLASH_003",
                "hours_worked": Decimal("4.0"),
                "unit_price": Decimal("75.00")
            }
        ]
        
        lines = []
        for data in line_data:
            line_total = round(data['hours_worked'] * data['unit_price'], 2)
            line = InvoiceLine(**data, line_total=line_total)
            lines.append(line)
        
        self.invoices[invoice_id] = Invoice(
            invoice_id=invoice_id,
            project_name="BMW FLASH Project",
            billing_period="2024-12",
            total_amount=Decimal("2462.50"),
            status=InvoiceStatus.DRAFT,
            created_by="user_001",
            created_at=datetime.now() - timedelta(days=5),
            lines=lines,
            currency=Currency.EUR
        )
        
        self.invoice_lines.extend(lines)
        
        # Create audit log entries
        self.audit_logs = [
            AuditLog(
                log_id=1,
                user_id="user_002",
                action="CREATE_CLAUSE",
                details="Created clause FLASH_001",
                timestamp=datetime.now() - timedelta(days=30)
            ),
            AuditLog(
                log_id=2,
                user_id="user_001",
                action="GENERATE_INVOICE",
                details=f"Generated invoice {invoice_id}",
                timestamp=datetime.now() - timedelta(days=5)
            ),
            AuditLog(
                log_id=3,
                user_id="user_001",
                action="UPDATE_JIRA_TOKEN",
                details="Updated Jira PAT",
                timestamp=datetime.now() - timedelta(days=10)
            )
        ]

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, user_data: dict) -> User:
        user_id = f"user_{str(uuid.uuid4())[:8]}"
        user = User(
            user_id=user_id,
            created_at=datetime.now(),
            has_jira_token=bool(user_data.get('jira_token')),
            **{k: v for k, v in user_data.items() if k != 'jira_token'}
        )
        self.users[user_id] = user
        
        if user_data.get('jira_token'):
            self.user_tokens[user_id] = f"encrypted_{user_data['jira_token']}"
        
        return user
    
    def update_user_token(self, user_id: str, token: str) -> bool:
        if user_id in self.users:
            self.user_tokens[user_id] = f"encrypted_{token}"
            self.users[user_id].has_jira_token = True
            return True
        return False
    
    def list_users(self) -> List[User]:
        return list(self.users.values())
    
    # ========================================================================
    # LEGAL CLAUSE OPERATIONS
    # ========================================================================
    
    def get_clause(self, clause_id: str) -> Optional[LegalClause]:
        return self.legal_clauses.get(clause_id)
    
    def create_clause(self, clause_data: dict, created_by: str) -> LegalClause:
        clause = LegalClause(
            created_by=created_by,
            created_at=datetime.now(),
            is_active=True,
            **clause_data
        )
        self.legal_clauses[clause.clause_id] = clause
        return clause
    
    def update_clause(self, clause_id: str, updates: dict) -> Optional[LegalClause]:
        clause = self.legal_clauses.get(clause_id)
        if clause:
            for key, value in updates.items():
                if value is not None:
                    setattr(clause, key, value)
        return clause
    
    def list_clauses(self, active_only: bool = True) -> List[LegalClause]:
        clauses = list(self.legal_clauses.values())
        if active_only:
            clauses = [c for c in clauses if c.is_active]
        return clauses
    
    # ========================================================================
    # JIRA OPERATIONS
    # ========================================================================
    
    def get_jira_tickets(
        self,
        status: Optional[TicketStatus] = None,
        label: Optional[str] = None
    ) -> List[JiraTicket]:
        tickets = self.jira_tickets
        
        if status:
            tickets = [t for t in tickets if t.status == status]
        
        if label:
            tickets = [t for t in tickets if label in t.labels]
        
        return tickets
    
    # ========================================================================
    # INVOICE OPERATIONS
    # ========================================================================
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return self.invoices.get(invoice_id)
    
    def create_invoice(self, invoice_data: dict, lines: List[dict], created_by: str) -> Invoice:
        invoice_id = f"INV-{datetime.now().strftime('%Y-%m')}-{str(uuid.uuid4())[:3].upper()}"
        
        invoice_lines = []
        for idx, line_data in enumerate(lines, 1):
            # Calculate line_total before creating InvoiceLine
            line_total = round(line_data['hours_worked'] * line_data['unit_price'], 2)
            
            line = InvoiceLine(
                line_id=len(self.invoice_lines) + idx,
                invoice_id=invoice_id,
                line_total=line_total,
                **line_data
            )
            invoice_lines.append(line)
            self.invoice_lines.append(line)
        
        invoice = Invoice(
            invoice_id=invoice_id,
            created_by=created_by,
            created_at=datetime.now(),
            status=InvoiceStatus.DRAFT,
            lines=invoice_lines,
            **invoice_data
        )
        
        self.invoices[invoice_id] = invoice
        return invoice
    
    def update_invoice(self, invoice_id: str, updates: dict) -> Optional[Invoice]:
        invoice = self.invoices.get(invoice_id)
        if invoice:
            for key, value in updates.items():
                if value is not None:
                    setattr(invoice, key, value)
        return invoice
    
    def list_invoices(self, created_by: Optional[str] = None) -> List[Invoice]:
        invoices = list(self.invoices.values())
        if created_by:
            invoices = [i for i in invoices if i.created_by == created_by]
        return invoices
    
    # ========================================================================
    # AUDIT LOG OPERATIONS
    # ========================================================================
    
    def create_audit_log(self, user_id: str, action: str, details: str = None):
        log = AuditLog(
            log_id=len(self.audit_logs) + 1,
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.now()
        )
        self.audit_logs.append(log)
        return log
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[AuditLog]:
        logs = self.audit_logs
        
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        
        if action:
            logs = [l for l in logs if l.action == action]
        
        return logs


# Global database instance
db = MockDatabase()