from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class TitleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TitleResponse(BaseModel):
    id: int
    name: str
    short_name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversionActivityResponse(BaseModel):
    id: int
    title_id: int
    title_name: str
    output_format: str
    status: str
    output_filename: Optional[str]
    file_count: int
    created_at: datetime
    completed_at: Optional[datetime]


class DownloadResponse(BaseModel):
    id: int
    job_id: int
    title_name: str
    filename: str
    output_format: str
    downloaded_at: datetime


class SourceFileResponse(BaseModel):
    id: int
    title_id: int
    original_name: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
