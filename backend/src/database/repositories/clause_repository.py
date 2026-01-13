from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from .base import BaseRepository
from ..models import LegalClauseModel


class ClauseRepository(BaseRepository[LegalClauseModel]):
    """Repository for Legal Clause operations"""
    
    def __init__(self, db: Session):
        super().__init__(LegalClauseModel, db)
    
    def get_active_clauses(self) -> List[LegalClauseModel]:
        """Get all active legal clauses"""
        return self.db.query(LegalClauseModel).filter(
            LegalClauseModel.is_active == True
        ).all()
    
    def get_by_effective_date(self, date: datetime) -> List[LegalClauseModel]:
        """Get clauses effective on a specific date"""
        return self.db.query(LegalClauseModel).filter(
            LegalClauseModel.effective_date <= date,
            LegalClauseModel.is_active == True
        ).all()
    
    def deactivate(self, clause_id: str) -> bool:
        """Deactivate a clause instead of deleting it"""
        try:
            clause = self.get(clause_id)
            if clause:
                clause.is_active = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def activate(self, clause_id: str) -> bool:
        """Reactivate a clause"""
        try:
            clause = self.get(clause_id)
            if clause:
                clause.is_active = True
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_by_label(self, label: str) -> Optional[LegalClauseModel]:
        """
        Get clause by label (clause_id in this case)
        Used for matching Jira labels to clauses
        """
        return self.get(label)