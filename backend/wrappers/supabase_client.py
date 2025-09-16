from sqlalchemy.orm import Session
from backend.models import User
from backend.schemas import UserCreate, UserUpdate
from backend.core.database import SessionLocal, init_db

class SupabaseCRUD:
    def __init__(self):
        init_db()  # Create tables on app start

    def get_db(self):
        """Create a database session"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_record(self, db: Session, model: UserCreate):
        """Create a new user record"""
        db_user = User(name=model.name, age=model.age)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def read_record(self, db: Session, user_id: int):
        """Read a user record by ID"""
        return db.query(User).filter(User.id == user_id).first()

    def update_record(self, db: Session, user_id: int, model: UserUpdate):
        """Update an existing user record"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            if model.name:
                db_user.name = model.name
            if model.age:
                db_user.age = model.age
            db.commit()
            db.refresh(db_user)
        return db_user

    def delete_record(self, db: Session, user_id: int):
        """Delete a user record"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
        return db_user
