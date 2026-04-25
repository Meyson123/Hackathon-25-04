from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import uvicorn
import os

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
from routes import home, reg, auth, lc, posts, reports

app.include_router(home.router, tags=["home"])
app.include_router(reg.router, tags=["registration"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(lc.router, tags=["personal_cabinet"])
app.include_router(posts.router, tags=["posts"])
app.include_router(reports.router, tags=["reports"])

# Визуализация
@app.get("/viz")
async def visualization(request: Request):
    return templates.TemplateResponse("visualization.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)