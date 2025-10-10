from pydantic import BaseModel, HttpUrl, ConfigDict 
from datetime import datetime
from typing import List, Optional

class URLBase(BaseModel):
    original_url: HttpUrl

class URLCreate(URLBase):
    pass

class URLInfo(BaseModel):
    short_code: str
    short_url: str
    original_url: HttpUrl
    model_config = ConfigDict(from_attributes=True)

class ClickInfo(BaseModel):
    clicked_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class URLStats(URLInfo):
    total_clicks: int
    created_at: datetime
    last_clicked_at: Optional[datetime] = None
    recent_clicks: List[ClickInfo] = []
    model_config = ConfigDict(from_attributes=True)