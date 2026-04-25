from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
import sqlite3
import os
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/lc/admin/stats")
async def get_admin_stats():
    """API для получения статистики админ-панели"""
    conn = get_db_connection()
    try:
        # Общая статистика пользователей
        total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
        active_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'active'").fetchone()["count"]
        pending_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'pending'").fetchone()["count"]
        
        # Статистика по ролям
        roles_stats = {}
        for role in ['admin', 'smm', 'editor', 'observer', 'volunteer']:
            count = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = ?", (role,)).fetchone()["count"]
            roles_stats[role] = count
        
        # Статистика постов
        total_posts = conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()["count"]
        published_posts = conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'published'").fetchone()["count"]
        pending_posts = conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'pending_review'").fetchone()["count"]
        draft_posts = conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'draft'").fetchone()["count"]
        
        # Статистика за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        new_users_week = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= ?",
            (week_ago.isoformat(),)
        ).fetchone()["count"]
        
        new_posts_week = conn.execute(
            "SELECT COUNT(*) as count FROM posts WHERE created_at >= ?",
            (week_ago.isoformat(),)
        ).fetchone()["count"]
        
        # Топ пользователей по публикациям
        top_users = conn.execute("""
            SELECT u.username, u.role, COUNT(p.id) as post_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.author_id
            GROUP BY u.id
            ORDER BY post_count DESC
            LIMIT 10
        """).fetchall()
        
        # Последние пользователи
        recent_users = conn.execute("""
            SELECT username, email, role, status, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()
        
        return JSONResponse({
            "users": {
                "total": total_users,
                "active": active_users,
                "pending": pending_users,
                "new_this_week": new_users_week,
                "by_role": roles_stats
            },
            "posts": {
                "total": total_posts,
                "published": published_posts,
                "pending": pending_posts,
                "draft": draft_posts,
                "new_this_week": new_posts_week
            },
            "top_users": [dict(user) for user in top_users],
            "recent_users": [dict(user) for user in recent_users]
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()

@router.get("/lc")
async def lc(request: Request):
    # Проверка сессии
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth", status_code=303)

    # Получение данных пользователя
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (request.session["user_id"],)
        ).fetchone()

        if not user:
            request.session.clear()
            return RedirectResponse(url="/auth", status_code=303)

        # Серверная проверка статуса (не доверяем session/localStorage)
        if str(user["status"]) != "active":
            request.session.clear()
            return RedirectResponse(url="/auth", status_code=303)

        # Формирование данных для шаблона
        full_name = None
        try:
            if "full_name" in user.keys():
                full_name = user["full_name"]
        except Exception:
            full_name = None

        user_data = {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role'],
            "status": user['status'],
            "full_name": full_name or user["username"]
        }

    except Exception as e:
        request.session.clear()
        return RedirectResponse(url="/auth", status_code=303)
    finally:
        conn.close()

    role = str(user_data.get("role") or "")
    if role == "admin":
        template_name = "admin_dashboard.html"
    elif role == "volunteer":
        template_name = "volunteer_dashboard.html"
    elif role in ("editor", "smm"):
        template_name = "editor_dashboard.html"
    else:
        # Фолбэк: для остальных ролей пока отдаём общий кабинет
        template_name = "lc.html"

    return templates.TemplateResponse(template_name, {
        "request": request,
        "user": user_data
    })

@router.post("/lc/logout")
async def logout(request: Request):
    # Удаление сессии
    request.session.clear()
    return RedirectResponse(url="/auth", status_code=303)