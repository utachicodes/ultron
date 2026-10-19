"""Authentication and registration."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, rate_limit

router = APIRouter()

# ============================================================
# Auth
# ============================================================
@router.post("/auth/token", response_model=schemas.Token)
def login(form_data: dict, request: Request, db: Session = Depends(get_db)):
    rate_limit.check("login", rate_limit.client_ip(request), limit=10, window_seconds=60)
    user = auth.authenticate_user(db, form_data.get("email", ""), form_data.get("password", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.RegisterCreate, request: Request, db: Session = Depends(get_db)):
    rate_limit.check("register", rate_limit.client_ip(request), limit=5, window_seconds=300)
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=user_in.email,
        hashed_password=auth.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=models.UserRole.client,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
