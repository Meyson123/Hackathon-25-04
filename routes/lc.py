from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import sqlite3
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        template_name = "lc.html"
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