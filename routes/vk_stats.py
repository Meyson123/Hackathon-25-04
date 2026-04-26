from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_ROOT_DIR, "db", "mediahub.db")

router = APIRouter()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_session_user(conn: sqlite3.Connection, request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = conn.execute("SELECT id, role, status FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Not authenticated")
    if str(user["status"]) != "active":
        request.session.clear()
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def _require_smm_or_admin(conn: sqlite3.Connection, request: Request):
    user = _get_session_user(conn, request)
    if str(user["role"]) not in ("smm", "admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


@router.get("/api/vk/config")
async def vk_config_status(request: Request):
    """
    Returns whether VK posting integration is configured.
    Requires SMM/Admin.
    """
    conn = get_db_connection()
    try:
        _require_smm_or_admin(conn, request)
    finally:
        conn.close()

    # Ensure .env is loaded even if this module is imported outside `main.py`
    try:
        load_dotenv(os.path.join(_ROOT_DIR, ".env"), override=True)
    except Exception:
        pass

    token = os.getenv("VK_ACCESS_TOKEN")
    owner_id = os.getenv("VK_OWNER_ID")
    configured = bool(token and str(token).strip() and owner_id and str(owner_id).strip())
    missing = []
    if not (token and str(token).strip()):
        missing.append("VK_ACCESS_TOKEN")
    if not (owner_id and str(owner_id).strip()):
        missing.append("VK_OWNER_ID")
    return JSONResponse({"ok": True, "configured": configured, "missing": missing})


@router.post("/api/vk/stats/collect")
async def collect_vk_stats(
    request: Request,
    limit: int = 50,
    lookback_days: int = 14,
    mock: int = 0,
    mock_lo: int = 0,
    mock_hi: int = 10,
):
    """
    Manual trigger to collect VK analytics snapshots for recent publications.
    Requires SMM/Admin.
    """
    conn = get_db_connection()
    try:
        _require_smm_or_admin(conn, request)
    finally:
        conn.close()

    from vk_analytics import collect_mock_analytics_once_async, collect_vk_analytics_once_async

    try:
        if int(mock or 0) == 1:
            data = await collect_mock_analytics_once_async(
                db_path=DB_PATH,
                limit=int(limit),
                lookback_days=int(lookback_days),
                lo=int(mock_lo),
                hi=int(mock_hi),
            )
            return JSONResponse({"ok": True, **data})

        data = await collect_vk_analytics_once_async(db_path=DB_PATH, limit=int(limit), lookback_days=int(lookback_days))
        if int(data.get("configured") or 0) != 1:
            # Demo-friendly fallback: if VK isn't configured, generate mock stats
            mock_data = await collect_mock_analytics_once_async(
                db_path=DB_PATH,
                limit=int(limit),
                lookback_days=int(lookback_days),
                lo=int(mock_lo),
                hi=int(mock_hi),
            )
            return JSONResponse({"ok": True, **mock_data, "note": "VK is not configured; generated mock stats instead"})
        return JSONResponse({"ok": True, **data})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VK collect failed: {e}")


@router.get("/api/vk/stats/summary")
async def vk_stats_summary(request: Request, days: int = 7):
    """
    Returns summary for VK publications for the last N days.
    Requires SMM/Admin.
    """
    conn = get_db_connection()
    try:
        _require_smm_or_admin(conn, request)

        days = int(days)
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Invalid days")

        # Latest snapshot per publication, aggregated
        row = conn.execute(
            """
            WITH latest AS (
                SELECT
                    a.publication_id,
                    a.views,
                    a.reactions,
                    a.comments,
                    a.shares,
                    a.engagement_rate,
                    a.collected_at,
                    ROW_NUMBER() OVER (PARTITION BY a.publication_id ORDER BY a.collected_at DESC, a.id DESC) AS rn
                FROM analytics a
                JOIN publications p ON p.id = a.publication_id
                WHERE p.status = 'published'
                  AND (p.published_at IS NULL OR p.published_at >= datetime('now', ?))
            )
            SELECT
                COUNT(*) AS posts,
                COALESCE(SUM(views), 0) AS views,
                COALESCE(SUM(reactions), 0) AS reactions,
                COALESCE(SUM(comments), 0) AS comments,
                COALESCE(SUM(shares), 0) AS shares,
                AVG(engagement_rate) AS avg_er
            FROM latest
            WHERE rn = 1
            """,
            (f"-{days} days",),
        ).fetchone()

        return JSONResponse(
            {
                "ok": True,
                "days": days,
                "summary": dict(row) if row else {"posts": 0, "views": 0, "reactions": 0, "comments": 0, "shares": 0, "avg_er": None},
            }
        )
    finally:
        conn.close()


@router.get("/api/vk/stats/posts")
async def vk_stats_posts(request: Request, limit: int = 20, offset: int = 0):
    """
    List recent VK publications with latest analytics snapshot.
    Requires SMM/Admin.
    """
    conn = get_db_connection()
    try:
        _require_smm_or_admin(conn, request)

        limit = max(1, min(200, int(limit)))
        offset = max(0, int(offset))

        rows = conn.execute(
            """
            WITH latest AS (
                SELECT
                    a.*,
                    ROW_NUMBER() OVER (PARTITION BY a.publication_id ORDER BY a.collected_at DESC, a.id DESC) AS rn
                FROM analytics a
            )
            SELECT
                p.id AS publication_id,
                p.post_id AS local_post_id,
                p.external_post_id AS vk_post_id,
                p.published_at AS published_at,
                po.title AS title,
                l.views AS views,
                l.reactions AS reactions,
                l.comments AS comments,
                l.shares AS shares,
                l.engagement_rate AS engagement_rate,
                l.collected_at AS collected_at
            FROM publications p
            LEFT JOIN posts po ON po.id = p.post_id
            LEFT JOIN latest l ON l.publication_id = p.id AND l.rn = 1
            WHERE p.status = 'published'
              AND p.external_post_id IS NOT NULL
              AND TRIM(p.external_post_id) != ''
            ORDER BY COALESCE(p.published_at, p.id) DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

        return JSONResponse({"ok": True, "items": [dict(r) for r in rows], "limit": limit, "offset": offset})
    finally:
        conn.close()

