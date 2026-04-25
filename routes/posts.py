from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import sqlite3
import os
from datetime import datetime
import uuid

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files", "uploads")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _require_editor_or_smm(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id, role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if str(user["status"]) != "active":
            raise HTTPException(status_code=403, detail="Inactive user")
        if str(user["role"]) not in ("editor", "smm", "admin"):
            raise HTTPException(status_code=403, detail="Forbidden")
        return int(user["id"])
    finally:
        conn.close()


@router.post("/api/posts")
async def create_post(
    request: Request,
    text: str = Form(...),
    publish_at: str | None = Form(None),
    photo: UploadFile | None = File(None),
):
    author_id = _require_editor_or_smm(request)

    clean_text = (text or "").strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Empty text")

    title = clean_text.splitlines()[0].strip()
    if len(title) > 70:
        title = title[:70].rstrip() + "…"
    if not title:
        title = "Публикация"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status = "published"
    scheduled_at = None
    published_at = now

    if publish_at:
        # ожидаем datetime-local: "YYYY-MM-DDTHH:MM"
        try:
            dt = datetime.fromisoformat(publish_at)
            scheduled_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            status = "scheduled"
            published_at = None
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid publish_at")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO posts (title, content, status, author_id, scheduled_at, published_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, clean_text, status, author_id, scheduled_at, published_at, now, now),
        )
        post_id = cur.lastrowid

        if photo is not None and photo.filename:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                raise HTTPException(status_code=400, detail="Unsupported image type")

            fname = f"{uuid.uuid4().hex}{ext}"
            abs_path = os.path.join(UPLOAD_DIR, fname)

            content = await photo.read()
            with open(abs_path, "wb") as f:
                f.write(content)

            file_url = f"/files/uploads/{fname}"
            cur.execute(
                """
                INSERT INTO media_files (post_id, file_url, file_type, file_size)
                VALUES (?, ?, ?, ?)
                """,
                (post_id, file_url, photo.content_type, len(content)),
            )

        conn.commit()
        return JSONResponse({"ok": True, "id": post_id, "status": status})
    finally:
        conn.close()

