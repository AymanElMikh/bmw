from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations
    All specific repositories should inherit from this class
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            return self.db.query(self.model).filter(
                self.model.__table__.primary_key.columns.values()[0] == id
            ).first()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record"""
        try:
            db_obj = self.get(id)
            if db_obj:
                for key, value in obj_in.items():
                    if hasattr(db_obj, key) and value is not None:
                        setattr(db_obj, key, value)
                self.db.commit()
                self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def delete(self, id: Any) -> bool:
        """Delete a record"""
        try:
            db_obj = self.get(id)
            if db_obj:
                self.db.delete(db_obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def exists(self, id: Any) -> bool:
        """Check if a record exists"""
        return self.get(id) is not None
    
    def count(self) -> int:
        """Count all records"""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e