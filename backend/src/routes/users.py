"""
User Management Routes
"""
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from src.models import User, UserCreate, UserRole, JiraTokenRequest, SuccessResponse
from src.database import get_db, UserRepository, AuditRepository, UserRoleEnum
from .dependencies import get_current_user, get_admin_user
from .converters import convert_user_model


def register_routes(app: FastAPI):
    """Register user-related routes"""
    
    @app.get("/api/users/me", response_model=User, tags=["Users"])
    async def get_current_user_info(current_user: User = Depends(get_current_user)):
        """Get current authenticated user information"""
        return current_user
    
    
    @app.get("/api/users", response_model=List[User], tags=["Users"])
    async def list_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """List all users (Admin only)"""
        user_repo = UserRepository(db)
        user_models = user_repo.get_all()
        return [convert_user_model(u) for u in user_models]
    
    
    @app.post("/api/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
    async def create_user(
        user_data: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_admin_user)
    ):
        """Create a new user (Admin only)"""
        user_repo = UserRepository(db)
        audit_repo = AuditRepository(db)
        
        # Check if email already exists
        existing_user = user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Convert role to enum
        user_dict = user_data.dict()
        user_dict['role'] = UserRoleEnum(user_data.role.value)
        
        user_model = user_repo.create(user_dict)
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="CREATE_USER",
            details=f"Created user {user_model.user_id} ({user_model.email})"
        )
        
        return convert_user_model(user_model)
    
    
    @app.put("/api/users/jira-token", response_model=SuccessResponse, tags=["Users"])
    async def update_jira_token(
        token_request: JiraTokenRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Update user's Jira Personal Access Token"""
        user_repo = UserRepository(db)
        audit_repo = AuditRepository(db)
        
        success = user_repo.update_jira_token(current_user.user_id, token_request.token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update token"
            )
        
        # Log action
        audit_repo.log_action(
            user_id=current_user.user_id,
            action="UPDATE_JIRA_TOKEN",
            details="Updated Jira PAT"
        )
        
        return SuccessResponse(
            message="Jira token updated successfully",
            data={"has_token": True}
        )