# Hackathon-25-04

## Запуск (Windows / PowerShell)

### 1) Установка зависимостей

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Настройка окружения

Скопируйте пример и задайте секрет:

```powershell
copy .env.example .env
```

В файле `.env` обязательно укажите:
- `SECRET_KEY` (без этого приложение не запустится)

Опционально:
- `SESSION_HTTPS_ONLY=1` (если запускаете по HTTPS)
- `SESSION_SAMESITE=lax|strict|none`

### 3) Инициализация базы (опционально)

Если нужно создать базу и (в dev) тест-админа:

```powershell
$env:CREATE_TEST_ADMIN="1"
$env:TEST_ADMIN_PASSWORD="change-me"
py .\db\db.py
```

Если тест-админ не нужен — просто выполните:

```powershell
py .\db\db.py
```

### 4) Запуск сервера

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Откройте:
- `/` или `/home`
- `/auth` (вход)
- `/lc` (личный кабинет, требует `status=active`)