from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from .base import BaseRepository
from ..models import AuditLogModel


class AuditRepository(BaseRepository[AuditLogModel]):
    """Repository for Audit Log operations"""
    
    def __init__(self, db: Session):
        super().__init__(AuditLogModel, db)
    
    def get_by_user(self, user_id: str) -> List[AuditLogModel]:
        """Get all audit logs for a specific user"""
        return self.db.query(AuditLogModel).filter(
            AuditLogModel.user_id == user_id
        ).order_by(AuditLogModel.timestamp.desc()).all()
    
    def get_by_action(self, action: str) -> List[AuditLogModel]:
        """Get all audit logs for a specific action"""
        return self.db.query(AuditLogModel).filter(
            AuditLogModel.action == action
        ).order_by(AuditLogModel.timestamp.desc()).all()
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[AuditLogModel]:
        """Get audit logs within a date range"""
        return self.db.query(AuditLogModel).filter(
            AuditLogModel.timestamp >= start_date,
            AuditLogModel.timestamp <= end_date
        ).order_by(AuditLogModel.timestamp.desc()).all()
    
    def get_recent(self, limit: int = 50) -> List[AuditLogModel]:
        """Get the most recent audit logs"""
        return self.db.query(AuditLogModel).order_by(
            AuditLogModel.timestamp.desc()
        ).limit(limit).all()
    
    def log_action(
        self,
        user_id: str,
        action: str,
        details: Optional[str] = None
    ) -> AuditLogModel:
        """Create a new audit log entry"""
        log = AuditLogModel(
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log