"""
Script to seed the database with initial data
Run with: python -m src.database.seed (from backend root)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from src.database import SessionLocal, init_db
from src.database.repositories import (
    UserRepository,
    ClauseRepository,
    TicketRepository,
    InvoiceRepository,
    AuditRepository
)
from src.database.models import UserRoleEnum, TicketStatusEnum, InvoiceStatusEnum, CurrencyEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_users(db):
    """Seed initial users"""
    user_repo = UserRepository(db)
    
    users_data = [
        {
            "user_id": "user_001",
            "name": "John Doe",
            "email": "john.doe@altran.com",
            "role": UserRoleEnum.PROJECT_LEADER,  # ✅ UPPER_CASE
            "has_jira_token": True
        },
        {
            "user_id": "user_002",
            "name": "Jane Smith",
            "email": "jane.smith@altran.com",
            "role": UserRoleEnum.ADMIN,  # ✅ UPPER_CASE
            "has_jira_token": True
        },
        {
            "user_id": "user_003",
            "name": "Bob Wilson",
            "email": "bob.wilson@altran.com",
            "role": UserRoleEnum.VIEWER,  # ✅ UPPER_CASE
            "has_jira_token": False
        }
    ]
    
    for user_data in users_data:
        if not user_repo.get(user_data["user_id"]):
            user_repo.create(user_data)
            logger.info(f"Created user: {user_data['email']}")
            
            # Add mock tokens for users with tokens
            if user_data["has_jira_token"]:
                user_repo.update_jira_token(
                    user_data["user_id"],
                    f"encrypted_token_{user_data['user_id']}"
                )


def seed_clauses(db):
    """Seed initial legal clauses"""
    clause_repo = ClauseRepository(db)
    
    clauses_data = [
        {
            "clause_id": "FLASH_001",
            "clause_name": "Standard Development",
            "description": "Regular software development work",
            "unit_price": Decimal("85.00"),
            "currency": CurrencyEnum.EUR,
            "effective_date": datetime(2024, 1, 1),
            "created_by": "user_002",
            "is_active": True
        },
        {
            "clause_id": "FLASH_002",
            "clause_name": "Bug Fixing",
            "description": "Critical bug resolution",
            "unit_price": Decimal("95.00"),
            "currency": CurrencyEnum.EUR,
            "effective_date": datetime(2024, 1, 1),
            "created_by": "user_002",
            "is_active": True
        },
        {
            "clause_id": "FLASH_003",
            "clause_name": "Code Review",
            "description": "Peer code review and quality assurance",
            "unit_price": Decimal("75.00"),
            "currency": CurrencyEnum.EUR,
            "effective_date": datetime(2024, 1, 1),
            "created_by": "user_002",
            "is_active": True
        },
        {
            "clause_id": "FLASH_004",
            "clause_name": "Technical Documentation",
            "description": "Technical writing and documentation",
            "unit_price": Decimal("70.00"),
            "currency": CurrencyEnum.EUR,
            "effective_date": datetime(2024, 1, 1),
            "created_by": "user_002",
            "is_active": True
        }
    ]
    
    for clause_data in clauses_data:
        if not clause_repo.get(clause_data["clause_id"]):
            clause_repo.create(clause_data)
            logger.info(f"Created clause: {clause_data['clause_id']}")


def seed_tickets(db):
    """Seed initial Jira tickets"""
    ticket_repo = TicketRepository(db)
    
    tickets_data = [
        {
            "ticket_id": "BMW-101",
            "summary": "Implement user authentication module",
            "description": "Add OAuth2 authentication",
            "status": TicketStatusEnum.CLOSED,
            "hours_worked": Decimal("16.5"),
            "labels": "FLASH_001",
            "assignee": "john.doe@altran.com",
            "resolved_at": datetime.now(timezone.utc) - timedelta(days=10),
            "clause_id": "FLASH_001",
            "billable_amount": Decimal("1402.50"),
            "is_billable": True
        },
        {
            "ticket_id": "BMW-102",
            "summary": "Fix payment gateway bug",
            "description": "Critical issue with payment processing",
            "status": TicketStatusEnum.CLOSED,
            "hours_worked": Decimal("8.0"),
            "labels": "FLASH_002",
            "assignee": "john.doe@altran.com",
            "resolved_at": datetime.now(timezone.utc) - timedelta(days=8),
            "clause_id": "FLASH_002",
            "billable_amount": Decimal("760.00"),
            "is_billable": True
        },
        {
            "ticket_id": "BMW-103",
            "summary": "Code review for PR #234",
            "description": "Review authentication changes",
            "status": TicketStatusEnum.CLOSED,
            "hours_worked": Decimal("4.0"),
            "labels": "FLASH_003",
            "assignee": "jane.smith@altran.com",
            "resolved_at": datetime.now(timezone.utc) - timedelta(days=7),
            "clause_id": "FLASH_003",
            "billable_amount": Decimal("300.00"),
            "is_billable": True
        },
        {
            "ticket_id": "BMW-104",
            "summary": "Update API documentation",
            "description": "Document new endpoints",
            "status": TicketStatusEnum.CLOSED,
            "hours_worked": Decimal("6.5"),
            "labels": "FLASH_004",
            "assignee": "john.doe@altran.com",
            "resolved_at": datetime.now(timezone.utc) - timedelta(days=5),
            "clause_id": "FLASH_004",
            "billable_amount": Decimal("455.00"),
            "is_billable": True
        },
        {
            "ticket_id": "BMW-105",
            "summary": "Refactor database queries",
            "description": "Optimize slow queries",
            "status": TicketStatusEnum.IN_PROGRESS,
            "hours_worked": Decimal("12.0"),
            "labels": "FLASH_001",
            "assignee": "john.doe@altran.com",
            "resolved_at": None,
            "clause_id": None,
            "billable_amount": Decimal("0.00"),
            "is_billable": False
        },
        {
            "ticket_id": "BMW-106",
            "summary": "Internal research task",
            "description": "Research new framework",
            "status": TicketStatusEnum.CLOSED,
            "hours_worked": Decimal("8.0"),
            "labels": "",
            "assignee": "bob.wilson@altran.com",
            "resolved_at": datetime.now(timezone.utc) - timedelta(days=3),
            "clause_id": None,
            "billable_amount": Decimal("0.00"),
            "is_billable": False
        }
    ]
    
    for ticket_data in tickets_data:
        if not ticket_repo.get(ticket_data["ticket_id"]):
            ticket_repo.create(ticket_data)
            logger.info(f"Created ticket: {ticket_data['ticket_id']}")


def seed_invoices(db):
    """Seed initial invoice"""
    invoice_repo = InvoiceRepository(db)
    
    invoice_id = "INV-2024-12-001"
    
    if not invoice_repo.get(invoice_id):
        invoice_data = {
            "invoice_id": invoice_id,
            "project_name": "BMW FLASH Project",
            "billing_period": "2024-12",
            "total_amount": Decimal("2462.50"),
            "currency": CurrencyEnum.EUR,
            "status": InvoiceStatusEnum.DRAFT,
            "created_by": "user_001"
        }
        
        lines_data = [
            {
                "jira_ticket_id": "BMW-101",
                "clause_id": "FLASH_001",
                "hours_worked": Decimal("16.5"),
                "unit_price": Decimal("85.00"),
                "line_total": Decimal("1402.50")
            },
            {
                "jira_ticket_id": "BMW-102",
                "clause_id": "FLASH_002",
                "hours_worked": Decimal("8.0"),
                "unit_price": Decimal("95.00"),
                "line_total": Decimal("760.00")
            },
            {
                "jira_ticket_id": "BMW-103",
                "clause_id": "FLASH_003",
                "hours_worked": Decimal("4.0"),
                "unit_price": Decimal("75.00"),
                "line_total": Decimal("300.00")
            }
        ]
        
        invoice_repo.create_with_lines(invoice_data, lines_data)
        logger.info(f"Created invoice: {invoice_id}")


def seed_audit_logs(db):
    """Seed initial audit logs"""
    audit_repo = AuditRepository(db)
    
    logs_data = [
        {
            "user_id": "user_002",
            "action": "CREATE_CLAUSE",
            "details": "Created clause FLASH_001"
        },
        {
            "user_id": "user_001",
            "action": "GENERATE_INVOICE",
            "details": "Generated invoice INV-2024-12-001"
        },
        {
            "user_id": "user_001",
            "action": "UPDATE_JIRA_TOKEN",
            "details": "Updated Jira PAT"
        }
    ]
    
    for log_data in logs_data:
        audit_repo.log_action(**log_data)
    
    logger.info(f"Created {len(logs_data)} audit log entries")


def seed_database():
    """Main seeding function"""
    logger.info("Starting database seeding...")
    
    # Initialize database (create tables)
    init_db()
    logger.info("Database tables created")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed all data
        seed_users(db)
        seed_clauses(db)
        seed_tickets(db)
        seed_invoices(db)
        seed_audit_logs(db)
        
        logger.info("Database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()