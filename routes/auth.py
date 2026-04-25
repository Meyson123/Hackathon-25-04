from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import sqlite3
import bcrypt
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/auth")
async def auth(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@router.post("/auth")
async def auth_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # Поиск пользователя
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "error": "Неверное имя пользователя или пароль"
            })

        # Проверка пароля
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "error": "Неверное имя пользователя или пароль"
            })

        # Создание сессии
        request.session["user_id"] = user['id']
        request.session["username"] = user['username']
        request.session["email"] = user['email']
        request.session["role"] = user['role']
        request.session["status"] = user['status']

    except Exception as e:
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "error": f"Ошибка при авторизации: {str(e)}"
        })
    finally:
        conn.close()

    return RedirectResponse(url="/lc", status_code=303)