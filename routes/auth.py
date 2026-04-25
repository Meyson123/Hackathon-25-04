from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import sqlite3
import bcrypt
import os
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")
logger = logging.getLogger(__name__)

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

        # Статус должен позволять вход (pending/blocked — запрещаем)
        status = str(user["status"])
        if status != "active":
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "error": "Аккаунт ещё не активирован администратором"
            })

        # Создание сессии
        request.session["user_id"] = int(user['id'])
        request.session["username"] = str(user['username'])
        request.session["email"] = str(user['email'])
        request.session["role"] = str(user['role'])
        request.session["status"] = status
        
        response = RedirectResponse(url="/lc", status_code=303)
        return response

    except Exception as e:
        logger.exception("Auth failed")
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "error": "Ошибка при авторизации"
        })
    finally:
        conn.close()

    return RedirectResponse(url="/lc", status_code=303)