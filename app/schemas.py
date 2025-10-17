from pydantic import BaseModel, HttpUrl, ConfigDict, EmailStr
from datetime import datetime
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    urls: List["URLInfo"] = []
    model_config = ConfigDict(from_attributes=True)

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- URL Schemas (Updated) ---
class URLBase(BaseModel):
    original_url: HttpUrl

class URLCreate(URLBase):
    pass

class URLInfo(BaseModel):
    short_code: str
    short_url: str
    original_url: HttpUrl
    owner_id: Optional[int] = None
    is_active: bool
    
    # FIX: Add the created_at field to the response model
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Analytics Schemas ---
class ClickInfo(BaseModel):
    clicked_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class URLStats(URLInfo):
    total_clicks: int
    last_clicked_at: Optional[datetime] = None
    recent_clicks: List[ClickInfo] = []
    model_config = ConfigDict(from_attributes=True)