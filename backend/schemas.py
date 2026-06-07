from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    is_admin: Optional[bool] = False

class ChatResponse(BaseModel):
    answer: str
    session_id: str

class DatasetBase(BaseModel):
    filename: str
    size_bytes: int

class DatasetResponse(DatasetBase):
    id: int
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    session_id: str
    dataset_ids: Optional[str] = None
    user_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    session_id: str
    dataset_ids: Optional[str] = None
    title: str
    created_at: datetime

