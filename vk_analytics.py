"""
VK analytics collector.

Reads VK publications from the local DB (table `publications`) and stores metric snapshots
into `analytics` table.
"""

from __future__ import annotations

import asyncio
import os
import random
import sqlite3
from typing import Any, Dict, Optional

import httpx


def _env(name: str) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) and v.strip() else None


def _vk_config() -> Optional[dict]:
    token = _env("VK_ACCESS_TOKEN")
    owner_id_raw = _env("VK_OWNER_ID")
    api_v = _env("VK_API_VERSION") or "5.199"

    if not token or not owner_id_raw:
        return None

    try:
        raw = str(owner_id_raw).strip()
        if raw.lower().startswith(("club", "public", "group")):
            digits = "".join(ch for ch in raw if ch.isdigit())
            if not digits:
                raise ValueError("no digits in VK_OWNER_ID")
            owner_id = -int(digits)
        else:
            owner_id = int(raw)
    except Exception:
        return None

    return {"token": token, "owner_id": int(owner_id), "v": api_v}


async def _vk_api(method: str, params: dict, token: str, v: str) -> Any:
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


async def fetch_vk_post_metrics(*, owner_id: int, post_id: int, token: str, v: str) -> Dict[str, int]:
    """
    Returns dict with keys: views, reactions, comments, shares.
    """
    # wall.getById expects "ownerId_postId"
    posts = await _vk_api("wall.getById", {"posts": f"{owner_id}_{post_id}"}, token, v)
    if not isinstance(posts, list) or not posts:
        raise RuntimeError("VK wall.getById returned empty response")
    p = posts[0] if isinstance(posts[0], dict) else {}

    likes = int(((p.get("likes") or {}).get("count")) or 0)
    reposts = int(((p.get("reposts") or {}).get("count")) or 0)
    comments = int(((p.get("comments") or {}).get("count")) or 0)
    views = int(((p.get("views") or {}).get("count")) or 0)

    return {"views": views, "reactions": likes, "comments": comments, "shares": reposts}


def _compute_er(*, views: int, reactions: int, comments: int, shares: int) -> Optional[float]:
    if not views or views <= 0:
        return None
    return round(((reactions + comments + shares) / float(views)) * 100.0, 4)


async def collect_vk_analytics_once_async(
    *, db_path: str, limit: int = 50, lookback_days: int = 14
) -> Dict[str, int]:
    cfg = _vk_config()
    if not cfg:
        return {"configured": 0, "processed": 0, "inserted": 0}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                pub.id AS publication_id,
                pub.external_post_id AS external_post_id,
                pub.published_at AS published_at
            FROM publications pub
            WHERE pub.external_post_id IS NOT NULL
              AND TRIM(pub.external_post_id) != ''
              AND pub.status = 'published'
              AND (pub.published_at IS NULL OR pub.published_at >= datetime('now', ?))
            ORDER BY COALESCE(pub.published_at, pub.id) DESC
            LIMIT ?
            """,
            (f"-{int(lookback_days)} days", int(limit)),
        ).fetchall()

        processed = 0
        inserted = 0
        for r in rows:
            processed += 1
            try:
                post_id = int(str(r["external_post_id"]).strip())
            except Exception:
                continue

            metrics = await fetch_vk_post_metrics(
                owner_id=cfg["owner_id"],
                post_id=post_id,
                token=cfg["token"],
                v=cfg["v"],
            )

            er = _compute_er(
                views=int(metrics["views"]),
                reactions=int(metrics["reactions"]),
                comments=int(metrics["comments"]),
                shares=int(metrics["shares"]),
            )

            conn.execute(
                """
                INSERT INTO analytics (publication_id, views, reactions, comments, shares, engagement_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(r["publication_id"]),
                    int(metrics["views"]),
                    int(metrics["reactions"]),
                    int(metrics["comments"]),
                    int(metrics["shares"]),
                    er,
                ),
            )
            inserted += 1

        conn.commit()
        return {"configured": 1, "processed": processed, "inserted": inserted}
    finally:
        conn.close()


async def start_vk_analytics_collector(*, db_path: str) -> None:
    """
    Background task. Does nothing if VK is not configured.
    """
    cfg = _vk_config()
    if not cfg:
        return

    poll_seconds = int(_env("VK_STATS_POLL_SECONDS") or "600")
    limit = int(_env("VK_STATS_LIMIT") or "50")
    lookback_days = int(_env("VK_STATS_LOOKBACK_DAYS") or "14")

    # Small jitter so multiple workers don't stampede (if any).
    await asyncio.sleep(2.0)

    while True:
        try:
            await collect_vk_analytics_once_async(db_path=db_path, limit=limit, lookback_days=lookback_days)
        except Exception:
            # Silent fail: stats are best-effort.
            pass
        await asyncio.sleep(max(30, poll_seconds))


async def collect_mock_analytics_once_async(
    *, db_path: str, limit: int = 50, lookback_days: int = 14, lo: int = 0, hi: int = 10
) -> Dict[str, int]:
    """
    Demo helper: fill `analytics` with random values in [lo, hi] for recent publications.
    Does not require VK configuration.
    """
    lo = int(lo)
    hi = int(hi)
    if lo > hi:
        lo, hi = hi, lo

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                pub.id AS publication_id
            FROM publications pub
            WHERE pub.status = 'published'
              AND (pub.published_at IS NULL OR pub.published_at >= datetime('now', ?))
            ORDER BY COALESCE(pub.published_at, pub.id) DESC
            LIMIT ?
            """,
            (f"-{int(lookback_days)} days", int(limit)),
        ).fetchall()

        processed = 0
        inserted = 0

        for r in rows:
            processed += 1
            views = random.randint(lo, hi)
            reactions = random.randint(lo, hi)
            comments = random.randint(lo, hi)
            shares = random.randint(lo, hi)
            er = _compute_er(views=views, reactions=reactions, comments=comments, shares=shares)

            conn.execute(
                """
                INSERT INTO analytics (publication_id, views, reactions, comments, shares, engagement_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(r["publication_id"]), views, reactions, comments, shares, er),
            )
            inserted += 1

        conn.commit()
        return {"mock": 1, "processed": processed, "inserted": inserted, "lo": lo, "hi": hi}
    finally:
        conn.close()

