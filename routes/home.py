from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

# Optional integration: Google Sheets (public via API key or private via service account)
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from google_sheets import get_sheet_values_cached

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/")
async def home(request: Request):
    conn = get_db_connection()
    try:
        # Автопубликация постов, запланированных на уже наступившее время.
        # Раньше это делалось только через JS-пинг, из-за чего пост мог "не появляться"
        # на главной, пока кто-то не откроет страницу и не сработает таймер.
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """
                UPDATE posts
                SET status = 'published',
                    published_at = COALESCE(published_at, ?),
                    updated_at = ?
                WHERE status = 'scheduled'
                  AND scheduled_at IS NOT NULL
                  AND scheduled_at <= ?
                """,
                (now, now, now),
            )
            conn.commit()
        except Exception:
            # Если публикация по расписанию недоступна из-за схемы/конкурентного доступа,
            # не ломаем главную — просто показываем ленту как есть.
            pass

        # Получаем новости
        rows = conn.execute(
            """
            SELECT
                p.id,
                p.title,
                p.content,
                p.published_at,
                (
                    SELECT mf.file_url
                    FROM media_files mf
                    WHERE mf.post_id = p.id
                    ORDER BY mf.uploaded_at DESC
                    LIMIT 1
                ) AS image_url
            FROM posts p
            WHERE p.status = 'published'
            ORDER BY COALESCE(p.published_at, p.created_at) DESC
            LIMIT 12
            """
        ).fetchall()

        news_posts = []
        for row in rows:
            post_dict = dict(row)
            # Получаем теги для поста (если таблицы тегов уже созданы)
            try:
                tags = conn.execute(
                    """
                    SELECT t.name
                    FROM tags t
                    JOIN post_tags pt ON t.id = pt.tag_id
                    WHERE pt.post_id = ?
                    ORDER BY t.name
                    """,
                    (post_dict["id"],),
                ).fetchall()
                post_dict["tags"] = [tag["name"] for tag in tags]
            except Exception:
                post_dict["tags"] = []
            news_posts.append(post_dict)
    except Exception:
        # Если упало именно получение ленты (например, из-за несоответствия схемы),
        # лучше показать пустую ленту, чем ломать всю главную.
        news_posts = []
    
    # Получаем предстоящие мероприятия
    upcoming_events = []
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event_rows = conn.execute("""
            SELECT * FROM events 
            WHERE start_datetime >= ?
            ORDER BY start_datetime ASC
            LIMIT 5
        """, (current_time,)).fetchall()
        
        upcoming_events = [dict(row) for row in event_rows]
    except Exception:
        upcoming_events = []
    finally:
        conn.close()

    sheet_values = None
    sheet_error = None
    try:
        sheet_values, sheet_error = get_sheet_values_cached(ttl_seconds=60)
    except Exception as e:
        sheet_values = None
        sheet_error = str(e)

    sheet_headers = []
    sheet_rows = []
    if sheet_values and len(sheet_values) > 0:
        sheet_headers = sheet_values[0]
        sheet_rows = sheet_values[1:11]  # preview up to 10 rows

    return templates.TemplateResponse("home.html", {
        "request": request, 
        "news_posts": news_posts,
        "upcoming_events": upcoming_events,
        "sheet_headers": sheet_headers,
        "sheet_rows": sheet_rows,
        "sheet_error": sheet_error,
    })