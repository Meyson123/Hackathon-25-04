from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, DateTime, Float, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), server_default="editor")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts: Mapped[List["Post"]] = relationship(back_populates="author")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'editor', 'observer')", name="check_user_role"),
    )

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), server_default="#3b82f6")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts: Mapped[List["Post"]] = relationship(back_populates="category")

class Template(Base):
    __tablename__ = "templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[str]] = mapped_column(Text) # Храним как JSON строку
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts: Mapped[List["Post"]] = relationship(back_populates="template")

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("templates.id", ondelete="SET NULL"))
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author: Mapped["User"] = relationship(back_populates="posts")
    category: Mapped["Category"] = relationship(back_populates="posts")
    template: Mapped["Template"] = relationship(back_populates="posts")
    media: Mapped[List["MediaFile"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    publications: Mapped[List["Publication"]] = relationship(back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'scheduled', 'published', 'failed')", name="check_post_status"),
    )

class MediaFile(Base):
    __tablename__ = "media_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped["Post"] = relationship(back_populates="media")

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(255))
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    publications: Mapped[List["Publication"]] = relationship(back_populates="social_account")

class Publication(Base):
    __tablename__ = "publications"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    social_account_id: Mapped[int] = mapped_column(ForeignKey("social_accounts.id", ondelete="CASCADE"))
    external_post_id: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), server_default="scheduled")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    post: Mapped["Post"] = relationship(back_populates="publications")
    social_account: Mapped["SocialAccount"] = relationship(back_populates="publications")
    analytics: Mapped[List["Analytics"]] = relationship(back_populates="publication", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'published', 'failed')", name="check_pub_status"),
    )

class Analytics(Base):
    __tablename__ = "analytics"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    views: Mapped[int] = mapped_column(Integer, default=0)
    reactions: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float)

    publication: Mapped["Publication"] = relationship(back_populates="analytics")
