"""
Роутер для работы с мероприятиями (events)
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime
import pickle
import calendar

# Google OAuth imports
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Импорт модуля синхронизации с Google Calendar
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from google_calendar import GoogleCalendarSync, sync_calendar_events

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")


class EventResponse(BaseModel):
    """Модель ответа с данными события"""
    id: int
    google_event_id: str
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: str
    end_datetime: str
    all_day: int
    created_at: str
    updated_at: str


class SyncResponse(BaseModel):
    """Модель ответа синхронизации"""
    total: int
    added: int
    updated: int
    failed: int


def get_db_connection():
    """Создает подключение к базе данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/api/events/month/{year}/{month}", response_model=List[EventResponse])
async def get_events_for_month(year: int, month: int):
    """
    Получить все мероприятия за указанный месяц
    
    Args:
        year: Год (например, 2025)
        month: Месяц (1-12)
        
    Returns:
        Список мероприятий за месяц
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Месяц должен быть от 1 до 12")
    
    conn = get_db_connection()
    try:
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

        # В БД start_datetime может быть как "YYYY-MM-DD HH:MM:SS", так и ISO ("YYYY-MM-DDTHH:MM:SSZ").
        # SQLite date(...) корректно вытаскивает дату из обоих форматов.
        rows = conn.execute(
            """
            SELECT *
            FROM events
            WHERE date(start_datetime) >= date(?)
              AND date(start_datetime) <= date(?)
            ORDER BY start_datetime
            """,
            (start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении мероприятий: {str(e)}")
    finally:
        conn.close()


@router.get("/api/events/date/{date}", response_model=List[EventResponse])
async def get_events_for_date(date: str):
    """
    Получить мероприятия на конкретную дату
    
    Args:
        date: Дата в формате YYYY-MM-DD
        
    Returns:
        Список мероприятий на дату
    """
    try:
        # Валидация формата даты
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте YYYY-MM-DD")
    
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM events
            WHERE date(start_datetime) = date(?)
            ORDER BY start_datetime
            """,
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении мероприятий: {str(e)}")
    finally:
        conn.close()


@router.get("/api/events/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(limit: int = 10):
    """
    Получить предстоящие мероприятия
    
    Args:
        limit: Максимальное количество мероприятий (по умолчанию 10)
        
    Returns:
        Список предстоящих мероприятий
    """
    conn = get_db_connection()
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        rows = conn.execute("""
            SELECT * FROM events 
            WHERE start_datetime >= ?
            ORDER BY start_datetime ASC
            LIMIT ?
        """, (current_time, limit)).fetchall()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении мероприятий: {str(e)}")
    finally:
        conn.close()


@router.post("/api/events/sync", response_model=SyncResponse)
async def sync_events():
    """
    Синхронизировать мероприятия с Google Calendar
    
    Returns:
        Статистика синхронизации
    """
    try:
        stats = sync_calendar_events(DB_PATH)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при синхронизации: {str(e)}")


@router.get("/api/events/{event_id}", response_model=EventResponse)
async def get_event_by_id(event_id: int):
    """
    Получить мероприятие по ID
    
    Args:
        event_id: ID мероприятия
        
    Returns:
        Данные мероприятия
    """
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")
        
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении мероприятия: {str(e)}")
    finally:
        conn.close()


@router.get("/api/events/calendar-dates/{year}/{month}")
async def get_calendar_dates_with_events(year: int, month: int):
    """
    Получить список дат месяца, в которые есть мероприятия
    
    Args:
        year: Год
        month: Месяц (1-12)
        
    Returns:
        Список дат в формате YYYY-MM-DD
    """
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Месяц должен быть от 1 до 12")
    
    conn = get_db_connection()
    try:
        # Формируем начало и конец месяца
        start_date = f"{year}-{month:02d}-01 00:00:00"
        if month == 12:
            end_date = f"{year + 1}-01-01 00:00:00"
        else:
            end_date = f"{year}-{month + 1:02d}-01 00:00:00"
        
        rows = conn.execute("""
            SELECT DISTINCT DATE(start_datetime) as event_date
            FROM events 
            WHERE start_datetime >= ? AND start_datetime < ?
            ORDER BY event_date
        """, (start_date, end_date)).fetchall()
        
        dates = [row['event_date'] for row in rows]
        return {"dates": dates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении дат: {str(e)}")
    finally:
        conn.close()


# Google OAuth2 авторизация
@router.get("/auth/google")
async def google_auth(request: Request):
    """Начинает OAuth2 авторизацию с Google"""
    client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Не настроены Google OAuth credentials")
    
    # Создаем OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://127.0.0.1:8000/auth/google/callback"]
            }
        },
        scopes=GoogleCalendarSync.SCOPES
    )
    
    flow.redirect_uri = "http://127.0.0.1:8000/auth/google/callback"
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Сохраняем state в сессии
    request.session['oauth_state'] = state
    
    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback")
async def google_auth_callback(request: Request, code: str, state: str):
    """Обрабатывает callback от Google OAuth2"""
    client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Не настроены Google OAuth credentials")
    
    # Проверяем state
    if state != request.session.get('oauth_state'):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Создаем OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://127.0.0.1:8000/auth/google/callback"]
            }
        },
        scopes=GoogleCalendarSync.SCOPES
    )
    
    flow.redirect_uri = "http://127.0.0.1:8000/auth/google/callback"
    
    try:
        # Получаем токен
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Сохраняем токен в файл
        token_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'calendar_token.pickle')
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
        
        # Выводим refresh_token для сохранения в .env
        refresh_token = credentials.refresh_token
        print(f"\n{'='*60}")
        print(f"✅ OAuth2 авторизация успешна!")
        print(f"{'='*60}")
        print(f"Ваш REFRESH_TOKEN:")
        print(f"{refresh_token}")
        print(f"{'='*60}")
        print(f"Добавьте это в .env файл:")
        print(f"GOOGLE_CALENDAR_REFRESH_TOKEN={refresh_token}")
        print(f"{'='*60}\n")
        
        # Перенаправляем на главную страницу
        return RedirectResponse("/")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении токена: {str(e)}")
