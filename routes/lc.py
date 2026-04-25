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
            return RedirectResponse(url="/auth", status_code=303)

        # Формирование данных для шаблона
        user_data = {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role'],
            "status": user['status'],
            "full_name": user.get('full_name', user['username'])
        }

    except Exception as e:
        return RedirectResponse(url="/auth", status_code=303)
    finally:
        conn.close()

    return templates.TemplateResponse("lc.html", {
        "request": request,
        "user": user_data
    })

@router.post("/lc/logout")
async def logout(request: Request):
    # Удаление сессии
    request.session.clear()
    return RedirectResponse(url="/auth", status_code=303)