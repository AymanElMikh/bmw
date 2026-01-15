"""
Shared Route Dependencies
Authentication, authorization, and common utilities
"""
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.models import User, UserRole
from src.database import get_db, UserRepository
from .converters import convert_user_model


async def get_current_user(
    user_id: str = "user_001",  # TODO: Extract from JWT token
    db: Session = Depends(get_db)
) -> User:
    """
    Mock authentication - in production, validate JWT token
    Extract user_id from Authorization header and validate token
    """
    user_repo = UserRepository(db)
    user_model = user_repo.get(user_id)
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return convert_user_model(user_model)


async def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify user has admin role
    Used for admin-only endpoints
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user