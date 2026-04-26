"""
Small helper for reading values from Google Sheets.

Supports either:
- Public sheet via API key (GOOGLE_SHEETS_API_KEY)
- Private sheet via Service Account JSON file (GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE)
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None, "err": None}


def _env(name: str) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) and v.strip() else None


def _fetch_via_api_key(spreadsheet_id: str, a1_range: str, api_key: str) -> List[List[str]]:
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{a1_range}"
    resp = requests.get(url, params={"key": api_key}, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    values = payload.get("values") or []
    return [[str(c) for c in row] for row in values]


def _fetch_via_service_account(spreadsheet_id: str, a1_range: str, sa_file: str) -> List[List[str]]:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        sa_file,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=a1_range)
        .execute()
    )
    values = result.get("values") or []
    return [[str(c) for c in row] for row in values]


def get_sheet_values_cached(
    *,
    ttl_seconds: int = 60,
) -> Tuple[Optional[List[List[str]]], Optional[str]]:
    """
    Returns (values, error_message). Values is a 2D list as returned by Sheets API.
    If integration is not configured, returns (None, None).
    """

    now = time.time()
    if _CACHE["data"] is not None and (now - float(_CACHE["ts"])) < ttl_seconds:
        return _CACHE["data"], _CACHE["err"]

    spreadsheet_id = _env("GOOGLE_SHEETS_SPREADSHEET_ID")
    a1_range = _env("GOOGLE_SHEETS_RANGE") or "A1:Z50"
    api_key = _env("GOOGLE_SHEETS_API_KEY")
    sa_file = _env("GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE")

    # Not configured: don't treat as error.
    if not spreadsheet_id:
        _CACHE.update({"ts": now, "data": None, "err": None})
        return None, None

    try:
        if sa_file:
            values = _fetch_via_service_account(spreadsheet_id, a1_range, sa_file)
        elif api_key:
            values = _fetch_via_api_key(spreadsheet_id, a1_range, api_key)
        else:
            raise RuntimeError(
                "Google Sheets is partially configured: set GOOGLE_SHEETS_API_KEY for public sheets "
                "or GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE for private sheets."
            )

        _CACHE.update({"ts": now, "data": values, "err": None})
        return values, None
    except Exception as e:
        msg = str(e)
        _CACHE.update({"ts": now, "data": None, "err": msg})
        return None, msg

