from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import uvicorn
import os
import sqlite3
import asyncio

# Загрузка переменных окружения (путь относительно корня проекта, не от cwd процесса)
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Переменные из файла .env в корне проекта должны иметь приоритет над пустыми/устаревшими значениями в окружении ОС.
load_dotenv(os.path.join(_ROOT_DIR, ".env"), override=True)

app = FastAPI(title="MediaHub")

# В проде нельзя стартовать с дефолтным secret: это позволяет подделывать сессии.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required (do not use a default value).")

# Middleware для сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=86400,
    same_site=os.getenv("SESSION_SAMESITE", "lax"),
    https_only=os.getenv("SESSION_HTTPS_ONLY", "0") == "1",
)

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/files", StaticFiles(directory="files"), name="files")

# Подключение роутеров
from routes import home, reg, auth, lc, posts, reports, events, vk_stats

app.include_router(home.router, tags=["home"])
app.include_router(reg.router, tags=["registration"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(lc.router, tags=["personal_cabinet"])
app.include_router(posts.router, tags=["posts"])
app.include_router(reports.router, tags=["reports"])
app.include_router(events.router, tags=["events"])
app.include_router(vk_stats.router, tags=["vk"])

# Визуализация
@app.get("/viz")
async def visualization(request: Request):
    return templates.TemplateResponse("visualization.html", {"request": request})

# Инициализация календаря при запуске
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    # Мягкая миграция: в ранних версиях базы могли отсутствовать таблицы тегов,
    # из-за чего падала главная и создание постов с тегами.
    db_path = os.path.join(_ROOT_DIR, "db", "mediahub.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS post_tags (
                post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (post_id, tag_id)
            );
            CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id);
            CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);

            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER REFERENCES publications(id) ON DELETE CASCADE,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                reactions INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                engagement_rate REAL
            );
            CREATE INDEX IF NOT EXISTS idx_analytics_publication_id ON analytics(publication_id);
            """
        )
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    from google_calendar import init_calendar
    
    init_calendar(db_path)

    # Фоновый сбор статистики VK (если настроено)
    try:
        from vk_analytics import start_vk_analytics_collector
        asyncio.create_task(start_vk_analytics_collector(db_path=db_path))
    except Exception:
        # Не ломаем запуск сервера, если VK не настроен/модуль не может стартовать
        pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)