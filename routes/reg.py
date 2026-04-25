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

@router.get("/reg")
async def reg(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@router.post("/reg")
async def reg_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    role: str = Form(default="volunteer")
):
    # Валидация
    if password != password2:
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "error": "Пароли не совпадают"
        })

    if len(password) < 6:
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "error": "Пароль должен содержать минимум 6 символов"
        })

    # Проверка существующего пользователя
    conn = get_db_connection()
    try:
        existing_user = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing_user:
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "error": "Пользователь с таким именем или email уже существует"
            })

        # Хеширование пароля
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Создание пользователя
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?)",
            (username, email, hashed_password, role, "pending")
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "error": f"Ошибка при регистрации: {str(e)}"
        })
    finally:
        conn.close()

    return RedirectResponse(url="/auth", status_code=303)