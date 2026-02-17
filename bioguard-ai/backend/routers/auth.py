"""Authentication router for login, logout, and user management."""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User
from auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_HOURS_ANALYZER,
    ACCESS_TOKEN_EXPIRE_DAYS_PI
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    device_id: Optional[str] = None
    village_id: Optional[str] = None
    village_name: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: UserResponse
    redirect_to: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    device_id: Optional[str] = None
    village_id: Optional[str] = None
    village_name: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Returns different token expiry times based on role:
    - Analyzer: 24 hours
    - Pi Sender: 30 days (Pi devices stay logged in)
    """
    # Authenticate user
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Create access token with role-specific expiry
    if user.role == "analyzer":
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS_ANALYZER)
    else:  # pi_sender
        expires_delta = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS_PI)
    
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "device_id": user.device_id,
        "village_id": user.village_id
    }
    
    access_token = create_access_token(data=token_data, expires_delta=expires_delta)
    
    # Determine redirect URL based on role
    redirect_to = "/dashboard" if user.role == "analyzer" else "/pi-sender"
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            device_id=user.device_id,
            village_id=user.village_id,
            village_name=user.village_name
        ),
        redirect_to=redirect_to
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (invalidate token).
    
    Note: Since we're using stateless JWT, actual token invalidation
    would require a token blacklist in Redis or similar. For now,
    this endpoint confirms logout and client should delete the token.
    """
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        device_id=current_user.device_id,
        village_id=current_user.village_id,
        village_name=current_user.village_name
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new user (admin only).
    
    Only existing analyzer users can create new accounts.
    This prevents public registration.
    """
    # Only analyzers can create new users
    if current_user.role != "analyzer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Analyzer users can create new accounts"
        )
    
    # Validate role
    if user_data.role not in ["analyzer", "pi_sender"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'analyzer' or 'pi_sender'"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        device_id=user_data.device_id,
        village_id=user_data.village_id,
        village_name=user_data.village_name,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        device_id=new_user.device_id,
        village_id=new_user.village_id,
        village_name=new_user.village_name
    )
