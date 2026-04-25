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


def _require_authenticated_user(request: Request) -> tuple[int, str]:
    """Проверка авторизации для любого активного пользователя"""
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
        return int(user["id"]), str(user["role"])
    finally:
        conn.close()


@router.post("/api/posts")
async def create_post(
    request: Request,
    text: str = Form(...),
    publish_at: str | None = Form(None),
    photo: UploadFile | None = File(None),
):
    author_id, role = _require_authenticated_user(request)

    clean_text = (text or "").strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Empty text")

    title = clean_text.splitlines()[0].strip()
    if len(title) > 70:
        title = title[:70].rstrip() + "…"
    if not title:
        title = "Публикация"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Волонтеры создают посты на модерации, SMM и редакторы - сразу публикуют
    if role == "volunteer":
        status = "pending_review"
        scheduled_at = None
        published_at = None
    else:
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


@router.get("/api/posts/pending")
async def get_pending_posts(request: Request):
    """Получить посты на модерации (только для SMM)"""
    moderator_id = _require_editor_or_smm(request)

    conn = get_db_connection()
    try:
        posts = conn.execute("""
            SELECT
                p.id,
                p.title,
                p.content,
                p.status,
                p.created_at,
                u.username as author_name,
                u.role as author_role,
                mf.file_url,
                mf.file_type
            FROM posts p
            LEFT JOIN users u ON p.author_id = u.id
            LEFT JOIN media_files mf ON p.id = mf.post_id
            WHERE p.status = 'pending_review'
            ORDER BY p.created_at DESC
        """).fetchall()

        result = []
        for post in posts:
            post_dict = dict(post)
            # Группируем медиафайлы для поста
            if post_dict["file_url"]:
                post_dict["media"] = [{
                    "url": post_dict["file_url"],
                    "type": post_dict["file_type"]
                }]
            else:
                post_dict["media"] = []
            del post_dict["file_url"]
            del post_dict["file_type"]
            result.append(post_dict)

        return JSONResponse({"posts": result})
    finally:
        conn.close()


@router.post("/api/posts/{post_id}/moderate")
async def moderate_post(request: Request, post_id: int, action: str = Form(...)):
    """Модерация поста: approve (одобрить) или reject (отклонить)"""
    moderator_id = _require_editor_or_smm(request)

    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Invalid action")

    conn = get_db_connection()
    try:
        # Проверяем, что пост существует и на модерации
        post = conn.execute(
            "SELECT id, status, author_id FROM posts WHERE id = ?",
            (post_id,)
        ).fetchone()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post["status"] != "pending_review":
            raise HTTPException(status_code=400, detail="Post is not pending review")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if action == "approve":
            # Одобряем пост - публикуем его
            conn.execute(
                """
                UPDATE posts
                SET status = 'published', moderator_id = ?, published_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (moderator_id, now, now, post_id)
            )

            # Начисляем баллы волонтеру
            conn.execute(
                """
                UPDATE users
                SET points = points + 10
                WHERE id = ?
                """,
                (post["author_id"],)
            )
        else:
            # Отклоняем пост
            conn.execute(
                """
                UPDATE posts
                SET status = 'draft', moderator_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (moderator_id, now, post_id)
            )

        conn.commit()
        return JSONResponse({"ok": True, "action": action})
    finally:
        conn.close()


@router.post("/api/posts/{post_id}/schedule")
async def schedule_post(request: Request, post_id: int, delay_at: str = Form(...)):
    """Отложенная публикация поста"""
    moderator_id = _require_editor_or_smm(request)

    try:
        dt = datetime.fromisoformat(delay_at)
        scheduled_at = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    conn = get_db_connection()
    try:
        # Проверяем, что пост существует и на модерации
        post = conn.execute(
            "SELECT id, status, author_id FROM posts WHERE id = ?",
            (post_id,)
        ).fetchone()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post["status"] != "pending_review":
            raise HTTPException(status_code=400, detail="Post is not pending review")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Планируем публикацию
        conn.execute(
            """
            UPDATE posts
            SET status = 'scheduled', moderator_id = ?, scheduled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (moderator_id, scheduled_at, now, post_id)
        )

        conn.commit()
        return JSONResponse({"ok": True, "scheduled_at": scheduled_at})
    finally:
        conn.close()


@router.get("/api/posts/my")
async def get_my_posts(request: Request, limit: int = 10, offset: int = 0):
    """Получить посты текущего пользователя"""
    user_id, role = _require_authenticated_user(request)

    conn = get_db_connection()
    try:
        posts = conn.execute("""
            SELECT
                p.id,
                p.title,
                p.content,
                p.status,
                p.created_at,
                p.published_at,
                mf.file_url,
                mf.file_type
            FROM posts p
            LEFT JOIN media_files mf ON p.id = mf.post_id
            WHERE p.author_id = ?
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset)).fetchall()

        result = []
        for post in posts:
            post_dict = dict(post)
            if post_dict["file_url"]:
                post_dict["media"] = [{
                    "url": post_dict["file_url"],
                    "type": post_dict["file_type"]
                }]
            else:
                post_dict["media"] = []
            del post_dict["file_url"]
            del post_dict["file_type"]
            result.append(post_dict)

        # Получаем общее количество постов
        total = conn.execute(
            "SELECT COUNT(*) as count FROM posts WHERE author_id = ?",
            (user_id,)
        ).fetchone()["count"]

        return JSONResponse({
            "posts": result,
            "total": total,
            "limit": limit,
            "offset": offset
        })
    finally:
        conn.close()


@router.get("/api/user/points")
async def get_user_points(request: Request):
    """Получить баллы текущего пользователя"""
    user_id, role = _require_authenticated_user(request)

    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT points FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse({"points": user["points"]})
    finally:
        conn.close()


@router.get("/api/user/ranking")
async def get_user_ranking(request: Request):
    """Получить место пользователя в рейтинге волонтеров"""
    user_id, role = _require_authenticated_user(request)

    conn = get_db_connection()
    try:
        # Получаем текущие баллы пользователя
        user = conn.execute(
            "SELECT points FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_points = user["points"]

        # Получаем количество волонтеров с баллами больше, чем у текущего пользователя
        rank = conn.execute(
            """
            SELECT COUNT(*) + 1 as rank
            FROM users
            WHERE role = 'volunteer' AND points > ?
            """,
            (user_points,)
        ).fetchone()["rank"]

        # Получаем общее количество волонтеров
        total_volunteers = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE role = 'volunteer'"
        ).fetchone()["count"]

        return JSONResponse({
            "rank": rank,
            "total": total_volunteers
        })
    finally:
        conn.close()


@router.post("/api/posts/publish-scheduled")
async def publish_scheduled_posts():
    """Публикация запланированных постов (вызывается автоматически)"""
    conn = get_db_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Находим все запланированные посты, время которых наступило
        scheduled_posts = conn.execute(
            """
            SELECT id, author_id, title, content
            FROM posts
            WHERE status = 'scheduled' AND scheduled_at <= ?
            """,
            (now,)
        ).fetchall()

        published_count = 0

        for post in scheduled_posts:
            # Публикуем пост
            conn.execute(
                """
                UPDATE posts
                SET status = 'published', published_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, post["id"])
            )

            # Если автор волонтер, начисляем баллы
            author = conn.execute(
                "SELECT role FROM users WHERE id = ?",
                (post["author_id"],)
            ).fetchone()

            if author and author["role"] == "volunteer":
                conn.execute(
                    """
                    UPDATE users
                    SET points = points + 10
                    WHERE id = ?
                    """,
                    (post["author_id"],)
                )

            published_count += 1

        conn.commit()
        return JSONResponse({
            "ok": True,
            "published_count": published_count,
            "timestamp": now
        })
    finally:
        conn.close()
