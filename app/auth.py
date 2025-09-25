from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import secrets
import os
from typing import Optional

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Internal authentication credentials (should be in environment variables)
INTERNAL_USERNAME = os.getenv("INTERNAL_USERNAME", "internal_service")
INTERNAL_PASSWORD = os.getenv("INTERNAL_PASSWORD", "internal_secret_key_2024")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str) -> User:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def verify_internal_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify internal service authentication"""
    is_correct_username = secrets.compare_digest(credentials.username, INTERNAL_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, INTERNAL_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current authenticated user, returns None if not authenticated"""
    try:
        # Check if Authorization header is present
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return None
        
        # Extract credentials from header
        import base64
        credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = credentials.split(":", 1)
        
        user = authenticate_user(db, username, password)
        return user
    except Exception:
        return None