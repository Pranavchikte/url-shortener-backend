from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated

# Import all our application modules
from . import database, models, schemas, crud, utils, security
from .worker import log_click_task

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# This allows our frontend to communicate with our backend.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://url-shortener-frontend-ctrl.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except security.JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- Authentication Endpoints ---

@app.post("/auth/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username) # The form uses 'username' for email
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected URL Shortening Endpoint ---

@app.post("/api/shorten", response_model=schemas.URLInfo)
def create_short_url(
    url: schemas.URLCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user) # <-- THIS PROTECTS THE ENDPOINT
):
    """Creates a short URL for the currently authenticated user."""
    try:
        short_code = utils.create_unique_short_code(db)
        db_url = crud.create_db_url(db, url, short_code, owner_id=current_user.id)
        
        base_url = str(request.base_url)
        db_url.short_url = f"{base_url}{short_code}"
        
        return db_url
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create a unique short code.")

# --- Public Endpoints ---

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

@app.get("/api/stats/{short_code}", response_model=schemas.URLStats)
def get_url_stats(short_code: str, request: Request, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_stats(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    base_url = str(request.base_url)
    db_url.short_url = f"{base_url}{short_code}"
    return db_url

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