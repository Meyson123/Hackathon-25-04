from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/")
async def home(request: Request):
    conn = get_db_connection()
    try:
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
            # Получаем теги для поста
            tags = conn.execute(
                """
                SELECT t.name
                FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = ?
                ORDER BY t.name
                """,
                (post_dict["id"],)
            ).fetchall()
            post_dict["tags"] = [tag["name"] for tag in tags]
            news_posts.append(post_dict)
    except Exception:
        news_posts = []
    finally:
        conn.close()

    return templates.TemplateResponse("home.html", {"request": request, "news_posts": news_posts})