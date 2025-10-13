from celery import Celery
from sqlalchemy.orm import Session
from . import crud, database
from .config import settings

celery_app = Celery(
    "url_shortener",
    broker=settings.REDIS_URL, 
    backend=settings.REDIS_URL
)

@celery_app.task
def log_click_task(short_code: str, ip_address: str, user_agent: str, referrer: str):
    
    db: Session = database.SessionLocal()
    try:
        crud.create_db_click(db, short_code, ip_address, user_agent, referrer)
        crud.update_db_url_clicks(db, short_code)
    finally:
        db.close()