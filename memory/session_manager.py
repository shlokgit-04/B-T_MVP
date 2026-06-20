from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.schemas import SessionState


SESSION_FILE = Path(__file__).resolve().parent.parent / "storage" / "sessions.json"


def _load_sessions() -> List[Dict[str, Any]]:
    if not SESSION_FILE.exists():
        return []
    try:
        with open(SESSION_FILE, "r") as f:
            data = f.read().strip()
            if not data:
                return []
            return json.loads(data)
    except (json.JSONDecodeError, IOError):
        return []


def _save_sessions(sessions: List[Dict[str, Any]]) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def _find_session(sessions: List[Dict[str, Any]], session_id: str) -> Optional[Dict[str, Any]]:
    for s in sessions:
        if s.get("session_id") == session_id:
            return s
    return None


def create_session(session_id: str) -> Dict[str, Any]:
    sessions = _load_sessions()

    existing = _find_session(sessions, session_id)
    if existing:
        return existing

    new_session = {
        "session_id": session_id,
        "entry_type": None,
        "data": {},
        "missing_fields": [],
        "completed": False,
        "saved": False,
        "confirmation_pending": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    sessions.append(new_session)
    _save_sessions(sessions)

    return new_session


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    sessions = _load_sessions()
    return _find_session(sessions, session_id)


def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sessions = _load_sessions()
    session = _find_session(sessions, session_id)

    if session is None:
        return None

    for key, value in updates.items():
        if key in ("session_id", "created_at"):
            continue
        session[key] = value

    session["updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_sessions(sessions)
    return session


def reset_session(session_id: str) -> Optional[Dict[str, Any]]:
    sessions = _load_sessions()
    session = _find_session(sessions, session_id)

    if session is None:
        return None

    session["entry_type"] = None
    session["data"] = {}
    session["missing_fields"] = []
    session["completed"] = False
    session["saved"] = False
    session["confirmation_pending"] = False
    session["updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_sessions(sessions)
    return session


def save_completed_entry(session_id: str) -> bool:
    sessions = _load_sessions()
    session = _find_session(sessions, session_id)

    if session is None:
        return False

    if not session.get("completed"):
        return False

    session["saved"] = True
    session["updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_sessions(sessions)
    return True


def to_session_state(session_data: Dict[str, Any]) -> SessionState:
    return SessionState(
        session_id=session_data["session_id"],
        entry_type=session_data.get("entry_type"),
        data=session_data.get("data", {}),
        missing_fields=session_data.get("missing_fields", []),
        completed=session_data.get("completed", False),
        saved=session_data.get("saved", False),
        confirmation_pending=session_data.get("confirmation_pending", False),
    )
