from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from . import database, models, schemas, crud, utils

from .worker import log_click_task


models.Base.metadata.create_all(bind=database.engine)

app =  FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000", # Default Next.js port
    "http://localhost:5173", # Default Vite port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/api/stats/{short_code}", response_model=schemas.URLStats)
def get_url_stats(short_code: str, request: Request, db: Session = Depends(get_db)):
   
    db_url = crud.get_db_url_stats(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    base_url = str(request.base_url)
    db_url.short_url = f"{base_url}{short_code}"
    
    return db_url
        
@app.get("/{short_code}", response_class=RedirectResponse)
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_by_short_code(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    if not db_url.is_active:
        raise HTTPException(status_code=410, detail="This link has been deactivated")
    
    log_click_task.delay(
        short_code=short_code,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )

    return RedirectResponse(url=db_url.original_url)
        
        
@app.post("/api/shorten", response_model=schemas.URLInfo)
def create_short_url(url: schemas.URLCreate, request: Request, db: Session = Depends(get_db)):
    
    try:
        short_code = utils.create_unique_short_code(db)
        
        db_url = crud.create_db_url(db, url, short_code)
        
        base_url = str(request.base_url)
        db_url.short_url = f"{base_url}{short_code}"
        
        return db_url
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create a unique short code.")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Hello World!"}