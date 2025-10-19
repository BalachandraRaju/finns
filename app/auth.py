"""
Authentication module for user management and session handling.
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)

# Pydantic models
class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Model for token payload data."""
    email: Optional[str] = None

class User(BaseModel):
    """Model for user data."""
    email: EmailStr
    full_name: str
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

# Password hashing functions using bcrypt directly
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError:
        return None

# Custom exception for authentication redirects
class AuthenticationRedirect(Exception):
    """Exception to trigger redirect to login page."""
    pass

# Session-based authentication for web pages
def get_current_user_from_session(request: Request):
    """Get current user from session cookie. Raises AuthenticationRedirect if not authenticated."""
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationRedirect("Not authenticated")

    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    token_data = decode_access_token(token)
    if token_data is None or token_data.email is None:
        raise AuthenticationRedirect("Invalid authentication credentials")

    # Import here to avoid circular dependency
    from app.user_service import get_user_by_email
    user = get_user_by_email(token_data.email)
    if user is None:
        raise AuthenticationRedirect("User not found")

    return user

# Optional authentication - returns None if not authenticated
def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from session cookie, returns None if not authenticated."""
    try:
        return get_current_user_from_session(request)
    except (HTTPException, AuthenticationRedirect):
        return None

# API token-based authentication
async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from Bearer token (for API endpoints)."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_access_token(credentials.credentials)
    if token_data is None or token_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from app.user_service import get_user_by_email
    user = get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

