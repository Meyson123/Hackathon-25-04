from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Схемы для Категорий
class CategoryBase(BaseModel):
    name: str
    slug: str
    color: str = "#3b82f6"

class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# Схемы для Пользователей
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "editor"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Схемы для Постов
class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    status: str = "draft"
    category_id: Optional[int] = None
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    author_id: Optional[int]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Схемы для Авторизации
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
