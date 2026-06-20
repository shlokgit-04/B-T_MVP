from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from data.labour_types import lookup_labour
from models.schemas import ExtractedEntity


def parse_labour(message: str) -> Tuple[Dict[str, Any], List[ExtractedEntity], float]:
    extracted: Dict[str, Any] = {}
    entities: List[ExtractedEntity] = []
    confidence = 0.0

    msg_lower = message.strip().lower()

    labour_type = _extract_labour_type(msg_lower)
    if labour_type:
        extracted["labour_type"] = labour_type
        entities.append(ExtractedEntity(field="labour_type", value=labour_type))
        confidence += 0.35
    else:
        labour_type = _extract_labour_type_fallback(msg_lower)
        if labour_type:
            extracted["labour_type"] = labour_type
            entities.append(ExtractedEntity(field="labour_type", value=labour_type))
            confidence += 0.2

    worker_count = _extract_worker_count(msg_lower)
    if worker_count is not None:
        extracted["worker_count"] = worker_count
        entities.append(ExtractedEntity(field="worker_count", value=worker_count))
        confidence += 0.3

    hours = _extract_hours(msg_lower)
    if hours is not None:
        extracted["hours"] = hours
        entities.append(ExtractedEntity(field="hours", value=hours))
        confidence += 0.25

    project = _extract_project(message)
    if project:
        extracted["project"] = project
        entities.append(ExtractedEntity(field="project", value=project))
        confidence += 0.2

    floor = _extract_floor(msg_lower)
    if floor:
        extracted["floor"] = floor
        entities.append(ExtractedEntity(field="floor", value=floor))
        confidence += 0.15

    activity = _extract_activity(msg_lower)
    if activity:
        extracted["activity"] = activity
        entities.append(ExtractedEntity(field="activity", value=activity))
        confidence += 0.1

    rate = _extract_rate(msg_lower)
    if rate is not None:
        extracted["rate"] = rate
        entities.append(ExtractedEntity(field="rate", value=rate))
        confidence += 0.2

    confidence = min(confidence, 1.0)
    confidence = round(confidence, 2)

    return extracted, entities, confidence


def _extract_labour_type(msg_lower: str) -> str | None:
    for labour_name in [
        "mason", "carpenter", "electrician", "plumber", "painter", "helper",
    ]:
        if labour_name in msg_lower:
            return labour_name

    if "steel fixer" in msg_lower or "steel fixers" in msg_lower:
        return "steel fixer"

    if "bar bender" in msg_lower:
        return "steel fixer"

    return None


def _extract_labour_type_fallback(msg_lower: str) -> str | None:
    words = msg_lower.split()
    for word in words:
        result = lookup_labour(word)
        if result:
            return result
    return None


def _extract_worker_count(msg_lower: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:mason|masons|carpenter|carpenters|helper|helpers|labour|labourer|worker|workers|fixer|fixers|electrician|plumber|painter)",
        r"(?:mason|masons|carpenter|carpenters|helper|helpers|labour|worker|workers|fixer|fixers)\s*[:#]?\s*(\d+)",
        r"(\d+)\s*(?:nos|no|people|persons|men|staff)",
        r"(?:added|deployed|assigned|hired)\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return int(match.group(1))

    return None


def _extract_hours(msg_lower: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)\s*(?:worked|of work|per day)?",
        r"(?:worked|for)\s*(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)",
        r"(\d+(?:\.\d+)?)\s*(?:hrs?)\s*(?:shift)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return float(match.group(1))
    return None


def _extract_project(message: str) -> str | None:
    patterns = [
        r"(?:for|at|project)\s+([A-Za-z0-9\s]+?)(?:\s+(?:floor|building|tower|phase|and|for)\b|$)",
        r"([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)\s+(?:tower|building|project)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if 2 < len(candidate) < 60:
                return candidate
    return None


def _extract_floor(msg_lower: str) -> str | None:
    floor_patterns = [
        r"(?:floor|fl)\s*[:#]?\s*(\d+|ground|basement|first|second|third|fourth|fifth|terrace|roof)",
        r"(?:on|for)\s+(?:the\s+)?(\d+|ground|basement|first|second|third|fourth|fifth)\s+(?:floor|fl)",
    ]
    for pattern in floor_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return match.group(1)
    return None


def _extract_activity(msg_lower: str) -> str | None:
    activity_keywords = [
        "foundation", "plastering", "plaster", "brickwork", "concreting",
        "shuttering", "reinforcement", "waterproofing", "tiling", "flooring",
        "painting", "finishing", "framing", "roofing", "masonry",
    ]
    for activity in activity_keywords:
        if activity in msg_lower:
            return activity
    return None


def _extract_rate(msg_lower: str) -> float | None:
    rate_patterns = [
        r"(?:rate|price|wage|@)\s*(?:is\s*)?(?:rs|inr|₹)?\s*(\d+(?:[,.]\d+)?)\s*(?:per|/|each|hour)?",
        r"(?:rs|inr|₹)\s*(\d+(?:[,.]\d+)?)\s*(?:per|/|each|hour)?",
        r"@\s*(\d+(?:[,.]\d+)?)",
    ]
    for pattern in rate_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            raw = match.group(1).replace(",", "")
            return float(raw)
    return None
