from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from memory.session_manager import (
    create_session,
    get_session,
    reset_session,
    save_completed_entry,
    to_session_state,
    update_session,
)
from models.schemas import ChatRequest, ChatResponse, ExtractedEntity, SessionResponse
from parser.equipment_parser import parse_equipment
from parser.intent_parser import detect_entry_type
from parser.labour_parser import parse_labour
from parser.material_parser import parse_material
from utils.field_checker import get_missing_fields, get_progress
from utils.question_generator import generate_summary, get_next_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("buildtrack-ai")

CONFIRM_WORDS = {"yes", "save", "confirm", "submit", "y", "ok", "yeah", "sure"}
DENY_WORDS = {"no", "cancel", "deny", "n", "nope", "never", "discard", "quit"}

app = FastAPI(
    title="BuildTrack AI MVP",
    description="A conversational AI assistant for construction site entry management.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PARSER_MAP = {
    "material": parse_material,
    "labour": parse_labour,
    "equipment": parse_equipment,
}


def _build_response(
    session_id: str,
    status: str,
    entry_type: str | None = None,
    message: str = "",
    extracted: Dict[str, Any] | None = None,
    missing_fields: List[str] | None = None,
    current_question: str | None = None,
    progress: int = 0,
    confidence: float = 0.0,
    entities: List[ExtractedEntity] | None = None,
    summary: str | None = None,
) -> ChatResponse:
    return ChatResponse(
        session_id=session_id,
        status=status,
        entry_type=entry_type,
        message=message,
        extracted=extracted or {},
        missing_fields=missing_fields or [],
        current_question=current_question,
        progress=progress,
        confidence=confidence,
        entities=entities or [],
        summary=summary,
    )


@app.get("/")
async def root():
    return {
        "service": "BuildTrack AI MVP",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /chat",
            "session": "GET /session/{session_id}",
            "reset": "POST /reset/{session_id}",
        },
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = create_session(session_id)
    if session is None:
        raise HTTPException(status_code=500, detail="Failed to create session")

    return _process_message(session, message)


@app.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_state(session_id: str):
    session_data = get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = to_session_state(session_data)
    return SessionResponse(session_id=session_id, state=state)


@app.post("/reset/{session_id}", response_model=SessionResponse)
async def reset_session_state(session_id: str):
    session_data = reset_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = to_session_state(session_data)
    return SessionResponse(session_id=session_id, state=state)


def _process_message(session: Dict[str, Any], message: str) -> ChatResponse:
    session_id = session["session_id"]
    current_data: Dict[str, Any] = session.get("data", {})
    entry_type: str | None = session.get("entry_type")
    confirmation_pending: bool = session.get("confirmation_pending", False)
    completed: bool = session.get("completed", False)

    if completed:
        return _handle_completed_session(session_id, message, session)

    if confirmation_pending:
        return _handle_confirmation(session_id, message, session)

    if entry_type is None:
        return _handle_initial_parsing(session_id, message, session)

    return _handle_follow_up(session_id, message, session, entry_type, current_data)


def _handle_initial_parsing(
    session_id: str, message: str, session: Dict[str, Any]
) -> ChatResponse:
    entry_type, confidence = detect_entry_type(message)

    if entry_type is None or confidence < 0.3:
        return _build_response(
            session_id=session_id,
            status="unknown",
            message="I couldn't determine what type of entry this is. Please specify if this is a material, labour, or equipment entry.",
            confidence=confidence,
        )

    parser_func = PARSER_MAP.get(entry_type)
    if parser_func is None:
        return _build_response(
            session_id=session_id,
            status="error",
            message=f"Sorry, I don't know how to handle '{entry_type}' entries yet.",
        )

    extracted, entities, parse_confidence = parser_func(message)
    combined_confidence = round((confidence + parse_confidence) / 2, 2)

    current_data = {}
    current_data.update(extracted)

    missing_fields = get_missing_fields(entry_type, current_data)
    progress = get_progress(entry_type, current_data)

    if not missing_fields:
        session = update_session(session_id, {
            "entry_type": entry_type,
            "data": current_data,
            "missing_fields": [],
            "completed": True,
            "confirmation_pending": True,
        })
        summary = generate_summary(entry_type, current_data)
        return _build_response(
            session_id=session_id,
            status="completed",
            entry_type=entry_type,
            message="All fields collected! Please review the summary below.",
            extracted=current_data,
            missing_fields=[],
            progress=100,
            confidence=combined_confidence,
            entities=entities,
            summary=summary,
            current_question="Would you like to save this entry? (yes/no)",
        )

    next_question = get_next_question(entry_type, missing_fields, current_data)

    session = update_session(session_id, {
        "entry_type": entry_type,
        "data": current_data,
        "missing_fields": missing_fields,
        "completed": False,
        "confirmation_pending": False,
    })

    return _build_response(
        session_id=session_id,
        status="incomplete",
        entry_type=entry_type,
        message=next_question or "Please provide more details.",
        extracted=current_data,
        missing_fields=missing_fields,
        current_question=next_question,
        progress=progress,
        confidence=combined_confidence,
        entities=entities,
    )


def _handle_follow_up(
    session_id: str,
    message: str,
    session: Dict[str, Any],
    entry_type: str,
    current_data: Dict[str, Any],
) -> ChatResponse:
    missing_fields: List[str] = session.get("missing_fields", [])
    answered_field: str | None = None

    if missing_fields:
        answered_field = missing_fields[0]
        parsed_value = _parse_field_value(entry_type, answered_field, message)

        if parsed_value is not None:
            current_data[answered_field] = parsed_value
        else:
            current_data[answered_field] = message

    parser_func = PARSER_MAP.get(entry_type)
    if parser_func:
        new_extracted, new_entities, _ = parser_func(message)
        previous_entities: List[ExtractedEntity] = []
        for field, value in current_data.items():
            if field not in new_extracted or new_extracted[field] != value:
                previous_entities.append(
                    ExtractedEntity(field=field, value=value, source="previous")
                )

        for field, value in new_extracted.items():
            if field == answered_field:
                continue
            already_set = current_data.get(field) is not None and current_data.get(field) != "" and current_data.get(field) != 0
            if already_set:
                continue
            if value is not None and value != "" and value != 0:
                current_data[field] = value

    updated_missing = get_missing_fields(entry_type, current_data)
    progress = get_progress(entry_type, current_data)

    if not updated_missing:
        session = update_session(session_id, {
            "data": current_data,
            "missing_fields": [],
            "completed": True,
            "confirmation_pending": True,
        })
        summary = generate_summary(entry_type, current_data)
        return _build_response(
            session_id=session_id,
            status="completed",
            entry_type=entry_type,
            message="All fields collected! Please review the summary below.",
            extracted=current_data,
            missing_fields=[],
            progress=100,
            confidence=1.0,
            entities=[],
            summary=summary,
            current_question="Would you like to save this entry? (yes/no)",
        )

    next_question = get_next_question(entry_type, updated_missing, current_data)

    session = update_session(session_id, {
        "data": current_data,
        "missing_fields": updated_missing,
    })

    return _build_response(
        session_id=session_id,
        status="incomplete",
        entry_type=entry_type,
        message=next_question or "Please provide more details.",
        extracted=current_data,
        missing_fields=updated_missing,
        current_question=next_question,
        progress=progress,
        confidence=1.0,
        entities=[],
    )


def _handle_confirmation(
    session_id: str, message: str, session: Dict[str, Any]
) -> ChatResponse:
    msg_lower = message.strip().lower()

    if msg_lower in CONFIRM_WORDS:
        saved = save_completed_entry(session_id)
        if saved:
            entry_type = session.get("entry_type", "unknown")
            data = session.get("data", {})
            _append_to_saved_entries(entry_type, data)
            return _build_response(
                session_id=session_id,
                status="saved",
                entry_type=entry_type,
                message="Entry has been saved successfully!",
                extracted=data,
                missing_fields=[],
                progress=100,
                summary=f"Entry saved. You can start a new entry or reset the session.",
            )
        else:
            return _build_response(
                session_id=session_id,
                status="error",
                message="Failed to save entry. Please try again.",
            )

    elif msg_lower in DENY_WORDS:
        reset_session(session_id)
        return _build_response(
            session_id=session_id,
            status="cancelled",
            message="Entry discarded. Session has been reset. You can start a new entry.",
            progress=0,
        )

    else:
        return _build_response(
            session_id=session_id,
            status="confirmation",
            message="Please confirm with 'yes' to save or 'no' to discard.",
            entry_type=session.get("entry_type"),
            extracted=session.get("data", {}),
            missing_fields=[],
            progress=100,
            current_question="Would you like to save this entry? (yes/no)",
        )


def _handle_completed_session(
    session_id: str, message: str, session: Dict[str, Any]
) -> ChatResponse:
    msg_lower = message.strip().lower()

    if msg_lower in CONFIRM_WORDS:
        saved = save_completed_entry(session_id)
        if saved:
            entry_type = session.get("entry_type", "unknown")
            data = session.get("data", {})
            _append_to_saved_entries(entry_type, data)
            return _build_response(
                session_id=session_id,
                status="saved",
                entry_type=entry_type,
                message="Entry has been saved successfully!",
                extracted=data,
                missing_fields=[],
                progress=100,
            )
        else:
            return _build_response(
                session_id=session_id,
                status="error",
                message="Failed to save entry. Please try again.",
            )

    elif msg_lower in DENY_WORDS:
        reset_session(session_id)
        return _build_response(
            session_id=session_id,
            status="cancelled",
            message="Entry discarded. Session has been reset.",
            progress=0,
        )

    else:
        summary = generate_summary(
            session.get("entry_type"), session.get("data", {})
        )
        return _build_response(
            session_id=session_id,
            status="completed",
            entry_type=session.get("entry_type"),
            message="An entry is ready to be saved.",
            extracted=session.get("data", {}),
            missing_fields=[],
            progress=100,
            summary=summary,
            current_question="Would you like to save this entry? (yes/no)",
        )


def _parse_field_value(entry_type: str, field: str, message: str):
    msg_lower = message.strip().lower()
    msg_original = message.strip()

    if field == "quantity":
        import re
        match = re.search(r"(\d+(?:[.,]\d+)?)", msg_lower)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    if field == "worker_count":
        import re
        match = re.search(r"(\d+)", msg_lower)
        if match:
            return int(match.group(1))
        return None

    if field in ("hours", "hours_used"):
        import re
        match = re.search(r"(\d+(?:[.,]\d+)?)", msg_lower)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    if field == "rate":
        import re
        match = re.search(r"(\d+(?:[.,]\d+)?)", msg_lower)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    if field == "floor":
        floor_map = {
            "ground": "Ground", "basement": "Basement",
            "first": "1", "second": "2", "third": "3",
            "fourth": "4", "fifth": "5", "terrace": "Terrace", "roof": "Roof",
        }
        import re
        floor_match = re.search(r"(\d+)", msg_lower)
        if floor_match:
            return floor_match.group(1)
        for word, mapped in floor_map.items():
            if word in msg_lower:
                return mapped
        return None

    if field == "activity":
        activities = [
            "foundation", "plastering", "plaster", "brickwork", "concreting",
            "shuttering", "reinforcement", "waterproofing", "tiling", "flooring",
            "painting", "finishing", "framing", "roofing", "masonry",
            "excavation", "earthwork", "levelling", "compaction",
        ]
        for activity in activities:
            if activity in msg_lower:
                return activity
        return None

    if field == "unit":
        from data.materials import normalize_unit
        unit = normalize_unit(msg_lower)
        if unit:
            return unit
        return None

    if field == "material_name":
        from data.materials import lookup_material
        mat = lookup_material(msg_lower)
        if mat:
            return mat
        return None

    if field == "labour_type":
        from data.labour_types import lookup_labour
        lbl = lookup_labour(msg_lower)
        if lbl:
            return lbl
        return None

    if field == "equipment_name":
        from data.equipment import lookup_equipment
        eq = lookup_equipment(msg_lower)
        if eq:
            return eq
        return None

    if field == "supplier":
        return msg_original

    if field == "operator":
        return msg_original

    if field == "project":
        return msg_original

    return msg_original


def _append_to_saved_entries(entry_type: str, data: Dict[str, Any]) -> None:
    saved_file = Path(__file__).resolve().parent / "storage" / "saved_entries.json"
    saved_file.parent.mkdir(parents=True, exist_ok=True)

    if saved_file.exists():
        try:
            with open(saved_file, "r") as f:
                entries = json.loads(f.read() or "[]")
        except (json.JSONDecodeError, IOError):
            entries = []
    else:
        entries = []

    entry = {
        "entry_type": entry_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)

    with open(saved_file, "w") as f:
        json.dump(entries, f, indent=2)

    logger.info(f"Saved {entry_type} entry: {data.get('material_name') or data.get('labour_type') or data.get('equipment_name')}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
