"""
Роутер для управления мероприятиями через админку
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")


class EventCreate(BaseModel):
    """Модель для создания мероприятия"""
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: str
    end_datetime: str
    all_day: int = 0


class EventUpdate(BaseModel):
    """Модель для обновления мероприятия"""
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    all_day: Optional[int] = None


def get_db_connection():
    """Создает подключение к базе данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/api/admin/events")
async def create_event(event: EventCreate):
    """Создать новое мероприятие"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO events (google_event_id, title, description, location, start_datetime, end_datetime, all_day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"manual_{datetime.now().timestamp()}",
            event.title,
            event.description,
            event.location,
            event.start_datetime,
            event.end_datetime,
            event.all_day
        ))
        conn.commit()
        
        return JSONResponse({
            "ok": True,
            "id": cursor.lastrowid,
            "message": "Мероприятие создано"
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании мероприятия: {str(e)}")
    finally:
        conn.close()


@router.put("/api/admin/events/{event_id}")
async def update_event(event_id: int, event: EventUpdate):
    """Обновить мероприятие"""
    conn = get_db_connection()
    try:
        # Проверяем существование
        existing = conn.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")
        
        # Формируем SQL динам
