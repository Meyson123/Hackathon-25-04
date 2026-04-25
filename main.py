from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import uvicorn
import os

# Загрузка переменных окружения
load_dotenv()

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

# Подключение роутеров
from routes import home, reg, auth, lc

app.include_router(home.router, tags=["home"])
app.include_router(reg.router, tags=["registration"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(lc.router, tags=["personal_cabinet"])

# Визуализация
@app.get("/viz")
async def visualization(request: Request):
    return templates.TemplateResponse("visualization.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)