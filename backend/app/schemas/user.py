from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr


class UserBase(BaseModel):
    """Base schema for User."""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str
    
class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None

class UserRead(UserBase):
    """Schema for reading user data."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )