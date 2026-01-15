"""
Audit Log Routes
"""
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.models import AuditLog, User, UserRole
from src.database import get_db, AuditRepository
from .dependencies import get_current_user, get_admin_user
from .converters import convert_audit_log_model


def register_routes(app: FastAPI):
    """Register audit log routes"""
    
    @app.get("/api/audit", response_model=List[AuditLog], tags=["Audit Logs"])
    async def list_audit_logs(
        user_id: str = None,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """List audit logs with optional filters (Admin only)"""
        audit_repo = AuditRepository(db)
        log_models = audit_repo.get_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date
        )
        return [convert_audit_log_model(l) for l in log_models]
    
    
    @app.get("/api/audit/me", response_model=List[AuditLog], tags=["Audit Logs"])
    async def list_my_audit_logs(
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """List current user's audit logs"""
        audit_repo = AuditRepository(db)
        log_models = audit_repo.get_logs(
            user_id=current_user.user_id,
            action=action,
            start_date=start_date,
            end_date=end_date
        )
        return [convert_audit_log_model(l) for l in log_models]
    
    
    @app.get("/api/audit/{log_id}", response_model=AuditLog, tags=["Audit Logs"])
    async def get_audit_log(
        log_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Get a specific audit log entry by ID (Admin only)"""
        audit_repo = AuditRepository(db)
        log_model = audit_repo.get(log_id)
        
        if not log_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return convert_audit_log_model(log_model)