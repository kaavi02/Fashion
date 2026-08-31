from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token, decode_access_token
)
from backend.app.models.models import User, UserMeasurement
from backend.app.schemas.schemas import (
    UserRegister, UserLogin, UserOut, UserProfileUpdate, Token,
    MeasurementInput, MeasurementOut
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retrieves current user if token is provided; otherwise returns None (for guest flows)."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
    
    if not raw_token:
        return None
    
    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        return None
    
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == int(user_id)).first()

def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Enforces authentication; raises 401 if unauthenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing, expired, or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new customer account."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    new_user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        address=user_in.address,
        city=user_in.city,
        state=user_in.state,
        postal_code=user_in.postal_code,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=new_user.id)
    return Token(access_token=token, user=UserOut.model_validate(new_user))

@router.post("/login", response_model=Token)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    """Authenticate customer with email & password, returning JWT access token."""
    user = db.query(User).filter(User.email == creds.email.lower()).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password"
        )
    
    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Get authenticated user profile details."""
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile and default delivery addresses."""
    for field, val in profile_in.model_dump(exclude_unset=True).items():
        setattr(current_user, field, val)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/measurements", response_model=Optional[MeasurementOut])
def get_user_measurements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve saved body measurements for AI Size Advisor."""
    return db.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.id).first()

@router.post("/measurements", response_model=MeasurementOut)
def save_user_measurements(
    meas_in: MeasurementInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save or update body measurements to user profile for instant AI sizing."""
    meas = db.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.id).first()
    if not meas:
        meas = UserMeasurement(user_id=current_user.id, **meas_in.model_dump())
        db.add(meas)
    else:
        for field, val in meas_in.model_dump().items():
            setattr(meas, field, val)
    db.commit()
    db.refresh(meas)
    return meas
