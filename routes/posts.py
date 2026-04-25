from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import sqlite3
import os
from datetime import datetime
import uuid
import httpx
from pydantic import BaseModel

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

router = APIRouter()

DB_PATH = os.path.join(_ROOT_DIR, "db", "mediahub.db")
UPLOAD_DIR = os.path.join(_ROOT_DIR, "files", "uploads")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _require_editor_or_smm(request: Request) -> sqlite3.Row:
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
        return user
    finally:
        conn.close()


def _require_authenticated(request: Request) -> sqlite3.Row:
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
        return user
    finally:
        conn.close()


def _vk_config():
    token = os.getenv("VK_ACCESS_TOKEN")
    owner_id = os.getenv("VK_OWNER_ID")
    api_v = os.getenv("VK_API_VERSION", "5.199")
    if not token:
        return None
    owner_id_int = None
    if owner_id:
        try:
            raw = str(owner_id).strip()
            # Allow common VK shortcuts like "club123", "public123", "group123"
            if raw.lower().startswith(("club", "public", "group")):
                digits = "".join(ch for ch in raw if ch.isdigit())
                if not digits:
                    raise ValueError("no digits in VK_OWNER_ID")
                owner_id_int = -int(digits)
            else:
                owner_id_int = int(raw)
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid VK_OWNER_ID")
    return {"token": str(token).strip(), "owner_id": owner_id_int, "v": str(api_v).strip()}


async def _vk_api(method: str, params: dict, token: str, v: str):
    url = f"https://api.vk.com/method/{method}"
    payload = dict(params)
    payload["access_token"] = token
    payload["v"] = v
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=payload)
        r.raise_for_status()
        data = r.json()
    if "error" in data:
        err = data["error"]
        msg = err.get("error_msg") or "VK API error"
        code = err.get("error_code")
        raise RuntimeError(f"VK error {code} at {method}: {msg}")
    return data.get("response")


async def _vk_upload_wall_photo(*, owner_id: int, token: str, v: str, abs_path: str) -> str:
    # For community tokens, use group_id (not owner_id) for upload server.
    if owner_id < 0:
        resp = await _vk_api("photos.getWallUploadServer", {"group_id": abs(owner_id)}, token, v)
    else:
        resp = await _vk_api("photos.getWallUploadServer", {"owner_id": owner_id}, token, v)
    upload_url = resp["upload_url"]

    async with httpx.AsyncClient(timeout=60) as client:
        with open(abs_path, "rb") as f:
            up = await client.post(upload_url, files={"photo": f})
        up.raise_for_status()
        up_data = up.json()

    save_params = {
        "photo": up_data["photo"],
        "server": up_data["server"],
        "hash": up_data["hash"],
    }
    if owner_id < 0:
        save_params["group_id"] = abs(owner_id)
    else:
        save_params["user_id"] = owner_id

    save = await _vk_api("photos.saveWallPhoto", save_params, token, v)
    if not isinstance(save, list) or not save:
        raise RuntimeError("VK photos.saveWallPhoto returned empty response; check token scopes (photos, wall) and owner_id")
    saved = save[0]
    return f"photo{saved['owner_id']}_{saved['id']}"


async def _vk_wall_post(*, owner_id: int, token: str, v: str, message: str, attachment: str | None):
    params = {"owner_id": owner_id, "message": message}
    if attachment:
        params["attachments"] = attachment
    if owner_id < 0:
        params["from_group"] = 1
    return await _vk_api("wall.post", params, token, v)


async def _vk_get_current_user_id(*, token: str, v: str) -> int:
    resp = await _vk_api("users.get", {}, token, v)
    if not isinstance(resp, list) or not resp:
        raise RuntimeError("VK users.get returned empty response; set VK_OWNER_ID explicitly or check token permissions")
    return int(resp[0]["id"])


@router.post("/api/posts")
async def create_post(
    request: Request,
    text: str = Form(...),
    publish_at: str | None = Form(None),
    photo: UploadFile | None = File(None),
):
    user = _require_editor_or_smm(request)
    author_id = int(user["id"])
    role = str(user["role"])

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
        local_image_abs_path = None

        if photo is not None and photo.filename:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                raise HTTPException(status_code=400, detail="Unsupported image type")

            fname = f"{uuid.uuid4().hex}{ext}"
            abs_path = os.path.join(UPLOAD_DIR, fname)
            local_image_abs_path = abs_path

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

        # Обработка тегов
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            for tag_name in tag_list:
                # Проверяем, существует ли тег
                tag = cur.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
                if not tag:
                    # Создаём новый тег
                    cur.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                    tag_id = cur.lastrowid
                else:
                    tag_id = tag["id"]
                # Связываем пост с тегом
                cur.execute(
                    "INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)",
                    (post_id, tag_id)
                )

        vk_result = None
        if (post_to_vk or "").lower() in ("1", "true", "on", "yes"):
            if str(user["role"]) not in ("smm", "admin"):
                raise HTTPException(status_code=403, detail="VK posting is only available for SMM role")
            cfg = _vk_config()
            if not cfg:
                raise HTTPException(status_code=500, detail="VK is not configured (VK_ACCESS_TOKEN)")
            if status != "published":
                raise HTTPException(status_code=400, detail="VK posting is only supported for immediate publishing")

            try:
                owner_id = cfg["owner_id"]
                if owner_id is None:
                    owner_id = await _vk_get_current_user_id(token=cfg["token"], v=cfg["v"])

                attachment = None
                vk_warning = None
                if local_image_abs_path:
                    try:
                        attachment = await _vk_upload_wall_photo(
                            owner_id=owner_id,
                            token=cfg["token"],
                            v=cfg["v"],
                            abs_path=local_image_abs_path,
                        )
                    except Exception as img_err:
                        # With community (group) tokens, VK may forbid upload server methods (error 27).
                        # In that case we still publish the text, but without the image.
                        msg = str(img_err)
                        if "VK error 27" in msg and owner_id < 0:
                            vk_warning = "VK rejected image upload for group token (error 27). Posted text without image."
                            attachment = None
                        else:
                            raise

                vk_result = await _vk_wall_post(
                    owner_id=owner_id,
                    token=cfg["token"],
                    v=cfg["v"],
                    message=clean_text,
                    attachment=attachment,
                )
                if vk_warning:
                    vk_result = dict(vk_result or {})
                    vk_result["warning"] = vk_warning

                cur.execute(
                    """
                    INSERT INTO publications (post_id, social_account_id, external_post_id, status, published_at)
                    VALUES (?, NULL, ?, 'published', ?)
                    """,
                    (post_id, str(vk_result.get("post_id")), now),
                )
            except Exception as e:
                cur.execute(
                    """
                    INSERT INTO publications (post_id, social_account_id, external_post_id, status, error_message, published_at)
                    VALUES (?, NULL, NULL, 'failed', ?, ?)
                    """,
                    (post_id, str(e), now),
                )
                raise HTTPException(status_code=502, detail=f"VK publish failed: {e}")

        conn.commit()
        return JSONResponse({"ok": True, "id": post_id, "status": status, "vk": vk_result})
    finally:
        conn.close()


class AiEditPostRequest(BaseModel):
    text: str


@router.post("/api/ai/edit-post")
async def ai_edit_post(request: Request, payload: AiEditPostRequest):
    """
    Proxy to local LLM server (OpenAI-compatible) to rewrite text as a social post.
    """
    _require_authenticated(request)

    base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
    model = os.getenv("LLM_MODEL")

    user_text = (payload.text or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty text")

    prompt = (
        "на основе этого текста сделай пост в соц сети, добавь эмодзи и хештеги\n\n"
        f"Текст:\n{user_text}"
    )

    req_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Ты SMM-редактор. Пиши по-русски. Дай готовый пост одним текстом."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    # Most local servers (LM Studio / Ollama OpenAI adapter) expose /v1/chat/completions
    url = f"{base_url}/v1/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if not model:
                m = await client.get(f"{base_url}/v1/models")
                m.raise_for_status()
                mdata = m.json()
                ids = [it.get("id") for it in (mdata.get("data") or []) if isinstance(it, dict)]
                # Prefer non-embedding models
                ids = [i for i in ids if i and "embed" not in str(i).lower()] or ids
                if not ids:
                    raise HTTPException(status_code=502, detail="No models available on LLM server")
                model = str(ids[0])
                req_body["model"] = model

            r = await client.post(url, json=req_body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    try:
        content = (data.get("choices") or [])[0]["message"]["content"]
    except Exception:
        content = None

    content = (content or "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="LLM returned empty response")

    return JSONResponse({"ok": True, "text": content})


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

            # Получаем теги поста
            tags = conn.execute("""
                SELECT t.name
                FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = ?
                ORDER BY t.name
            """, (post_dict["id"],)).fetchall()

            post_dict["tags"] = [tag["name"] for tag in tags]
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
        return JSONResponse({"ok": True, "id": post_id, "status": status, "vk": vk_result})
    finally:
        conn.close()

