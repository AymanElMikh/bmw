from typing import Optional, List
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import UserModel, UserTokenModel, UserRoleEnum


class UserRepository(BaseRepository[UserModel]):
    """Repository for User operations"""
    
    def __init__(self, db: Session):
        super().__init__(UserModel, db)
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    def get_by_role(self, role: UserRoleEnum) -> List[UserModel]:
        """Get all users with a specific role"""
        return self.db.query(UserModel).filter(UserModel.role == role).all()
    
    def update_jira_token(self, user_id: str, encrypted_token: str) -> bool:
        """Update or create user's Jira token"""
        try:
            # Check if token exists
            token = self.db.query(UserTokenModel).filter(
                UserTokenModel.user_id == user_id
            ).first()
            
            if token:
                token.encrypted_token = encrypted_token
            else:
                token = UserTokenModel(
                    user_id=user_id,
                    encrypted_token=encrypted_token
                )
                self.db.add(token)
            
            # Update user's has_jira_token flag
            user = self.get(user_id)
            if user:
                user.has_jira_token = True
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_jira_token(self, user_id: str) -> Optional[str]:
        """Get user's encrypted Jira token"""
        token = self.db.query(UserTokenModel).filter(
            UserTokenModel.user_id == user_id
        ).first()
        return token.encrypted_token if token else None
    
    def has_jira_token(self, user_id: str) -> bool:
        """Check if user has a Jira token configured"""
        user = self.get(user_id)
        return user.has_jira_token if user else False