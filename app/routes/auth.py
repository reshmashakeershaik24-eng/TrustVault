from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, generate_uuid, utc_now
from app.schemas import UserRegister, UserLogin, UserOut, Token
from app.security import verify_password, get_password_hash, create_access_token, get_current_user
from app.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
    
    # Enforce allowed roles
    role = user_in.role.upper()
    if role not in ["ADMIN", "OWNER", "VIEWER"]:
        role = "VIEWER"

    user = User(
        id=generate_uuid(),
        email=user_in.email.lower().strip(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=role,
        is_active=True,
        created_at=utc_now()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_REGISTERED",
        status="ALLOWED",
        user_id=user.id,
        user_email=user.email,
        details=f"New user registered with role {user.role}",
        request=request
    )
    return user

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    email_clean = login_in.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(login_in.password, user.hashed_password):
        # Audit refused login attempt
        log_audit_event(
            db=db,
            action="LOGIN",
            status="DENIED",
            user_id=user.id if user else None,
            user_email=email_clean,
            details="Invalid email or password",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        log_audit_event(
            db=db,
            action="LOGIN",
            status="DENIED",
            user_id=user.id,
            user_email=user.email,
            details="Deactivated account attempted login",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})

    log_audit_event(
        db=db,
        action="LOGIN",
        status="ALLOWED",
        user_id=user.id,
        user_email=user.email,
        details=f"Successful login as {user.role}",
        request=request
    )
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserOut])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List users for document sharing dropdown"""
    return db.query(User).filter(User.is_active == True).all()

