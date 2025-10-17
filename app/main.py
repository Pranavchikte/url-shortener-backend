from fastapi import FastAPI, Depends, HTTPException, Request, status, Request, status 
from fastapi.responses import RedirectResponse, JSONResponse
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


# New Endpoint

@app.get("/api/me/links", response_model=list[schemas.URLInfo])
def read_user_links(
    request: Request, # <-- ADD THE REQUEST DEPENDENCY
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # Get the list of URL objects from the database
    db_links = crud.get_user_links(db=db, owner_id=current_user.id)
    
    # Get the base URL (e.g., "http://localhost:8000/")
    base_url = str(request.base_url)
    
    # Manually add the 'short_url' attribute to each link object
    for link in db_links:
        link.short_url = f"{base_url}{link.short_code}"
        
    return db_links


# ADD THIS NEW ENDPOINT 
@app.get("/api/me/links/recent", response_model=list[schemas.URLInfo])
def read_user_recent_links(
    request: Request,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    db_links = crud.get_user_recent_links(db=db, owner_id=current_user.id)
    
    base_url = str(request.base_url)
    for link in db_links:
        link.short_url = f"{base_url}{link.short_code}"
        
    return db_links
# END OF NEW ENDPOINT 


# vvv ADD THIS NEW ENDPOINT vvv
@app.patch("/api/links/{short_code}", response_model=schemas.URLInfo)
def toggle_link_status(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    
    db_url = crud.update_db_url_status(db, short_code=short_code, owner_id=current_user.id)

    if not db_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or you do not have permission to modify it.",
        )
    
    # Manually construct the short_url before returning
    base_url = str(request.base_url)
    db_url.short_url = f"{base_url}{db_url.short_code}"

    return db_url
# ^^^ END OF NEW ENDPOINT ^^^


# New endpoint

@app.delete("/api/links/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    
    db_url = crud.delete_db_link(db, short_code=short_code, owner_id=current_user.id)

    if not db_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or you do not have permission to delete it.",
        )
    
    return
#  END OF NEW ENDPOINT 


# --- Protected URL Shortening Endpoint ---

@app.post("/api/shorten", response_model=schemas.URLInfo)
def create_short_url(
    url: schemas.URLCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user) # <-- THIS PROTECTS THE ENDPOINT
):
    
    try:
        short_code = utils.create_unique_short_code(db)
        db_url = crud.create_db_url(db, url, short_code, owner_id=current_user.id)
        
        base_url = str(request.base_url)
        db_url.short_url = f"{base_url}{short_code}"
        
        return db_url
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not create a unique short code.")

# --- Public Endpoints ---

@app.get("/{short_code}") # FIX: Removed response_class=RedirectResponse to allow for multiple response types
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_by_short_code(db, short_code)
    
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
        
    # FIX: This is the key change. We now handle the inactive link case manually.
    if not db_url.is_active:
        # Instead of a simple exception, we return a JSONResponse with cache-control headers.
        # This tells the browser: "Do not remember this error response."
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={"detail": "This link has been deactivated"},
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
        )
    
    # If the link is active, proceed as normal.
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