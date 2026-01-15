"""
Legal Clause Management Routes
"""
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from src.models import LegalClause, LegalClauseCreate, LegalClauseUpdate, SuccessResponse, User
from src.database import get_db, ClauseRepository, AuditRepository
from .dependencies import get_current_user, get_admin_user
from .converters import convert_clause_model


def register_routes(app: FastAPI):
    """Register legal clause routes"""
    
    @app.get("/api/clauses", response_model=List[LegalClause], tags=["Legal Clauses"])
    async def list_clauses(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """List all legal clauses"""
        clause_repo = ClauseRepository(db)
        clause_models = clause_repo.get_all()
        return [convert_clause_model(c) for c in clause_models]
    
    
    @app.post("/api/clauses", response_model=LegalClause, status_code=status.HTTP_201_CREATED, tags=["Legal Clauses"])
    async def create_clause(
        clause_data: LegalClauseCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Create a new legal clause (Admin only)"""
        clause_repo = ClauseRepository(db)
        audit_repo = AuditRepository(db)
        
        clause_model = clause_repo.create(clause_data.dict())
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="CREATE_CLAUSE",
            details=f"Created clause {clause_model.clause_id} ({clause_model.clause_name})"
        )
        
        return convert_clause_model(clause_model)
    
    
    @app.get("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
    async def get_clause(
        clause_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get a specific legal clause by ID"""
        clause_repo = ClauseRepository(db)
        clause_model = clause_repo.get(clause_id)
        
        if not clause_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clause not found"
            )
        
        return convert_clause_model(clause_model)
    
    
    @app.put("/api/clauses/{clause_id}", response_model=LegalClause, tags=["Legal Clauses"])
    async def update_clause(
        clause_id: str,
        clause_data: LegalClauseUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Update a legal clause (Admin only)"""
        clause_repo = ClauseRepository(db)
        audit_repo = AuditRepository(db)
        
        clause_model = clause_repo.update(clause_id, clause_data.dict())
        
        if not clause_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clause not found"
            )
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="UPDATE_CLAUSE",
            details=f"Updated clause {clause_model.clause_id} ({clause_model.clause_name})"
        )
        
        return convert_clause_model(clause_model)
    
    
    @app.delete("/api/clauses/{clause_id}", response_model=SuccessResponse, tags=["Legal Clauses"])
    async def delete_clause(
        clause_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Delete a legal clause (Admin only)"""
        clause_repo = ClauseRepository(db)
        audit_repo = AuditRepository(db)
        
        success = clause_repo.delete(clause_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clause not found"
            )
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="DELETE_CLAUSE",
            details=f"Deleted clause {clause_id}"
        )
        
        return SuccessResponse(
            message="Clause deleted successfully",
            data={"clause_id": clause_id}
        )