from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class User(Base):
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    urls = relationship("URL", back_populates="owner")


class URL(Base):
    
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    
    total_clicks = Column(Integer, default=0)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="urls")
    clicks = relationship("Click", back_populates="url")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), ForeignKey("urls.short_code"), nullable=False)
    
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    
    url = relationship("URL", back_populates="clicks")
