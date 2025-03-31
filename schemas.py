from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    password: str


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    short_code: str
    original_url: HttpUrl