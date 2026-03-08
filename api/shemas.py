from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- USER ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# --- PROGRESS ---
class ProgressCreate(BaseModel):
    phase: str
    completed: bool = False

class ProgressUpdate(BaseModel):
    phase: Optional[str] = None
    step: Optional[int] = None
    completed: Optional[bool] = None

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    phase: str
    step: Optional[int]
    completed: bool
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- CERTIFICATE ---
class CertificateResponse(BaseModel):
    user_id: int
    eligible: bool
    completed_phases: int
    message: str
