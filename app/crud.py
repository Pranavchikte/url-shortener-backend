# app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from . import models, schemas, security

# --- User CRUD Functions ---

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- URL CRUD Functions ---

def get_db_url_by_short_code(db: Session, short_code: str) -> models.URL | None:
    return db.query(models.URL).filter(models.URL.short_code == short_code).first()

def get_db_url_stats(db: Session, short_code: str) -> models.URL | None:
    db_url = get_db_url_by_short_code(db, short_code)
    if db_url:
        db_url.recent_clicks = (
            db.query(models.Click)
            .filter(models.Click.short_code == short_code)
            .order_by(models.Click.clicked_at.desc())
            .limit(10)
            .all()
        )
    return db_url

# vvv THIS IS THE CORRECTED FUNCTION vvv
def create_db_url(db: Session, url: schemas.URLCreate, short_code: str, owner_id: int) -> models.URL:
    """Creates a new URL entry and associates it with a user."""
    db_url = models.URL(
        original_url=str(url.original_url),
        short_code=short_code,
        owner_id=owner_id,  # FIX: Link the URL to the user
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url
# ^^^ END OF FIX ^^^

# --- Click CRUD Functions ---

def create_db_click(db: Session, short_code: str, ip: str, ua: str, ref: str):
    db_click = models.Click(
        short_code=short_code,
        ip_address=ip,
        user_agent=ua,
        referrer=ref,
    )
    db.add(db_click)
    db.commit()

def update_db_url_clicks(db: Session, short_code: str):
    db.query(models.URL).filter(models.URL.short_code == short_code).update({
        models.URL.total_clicks: models.URL.total_clicks + 1,
        models.URL.last_clicked_at: func.now(),
    })
    db.commit()