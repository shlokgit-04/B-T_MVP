from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from data.equipment import lookup_equipment
from models.schemas import ExtractedEntity


def parse_equipment(message: str) -> Tuple[Dict[str, Any], List[ExtractedEntity], float]:
    extracted: Dict[str, Any] = {}
    entities: List[ExtractedEntity] = []
    confidence = 0.0

    msg_lower = message.strip().lower()

    equipment_name = _extract_equipment_name(msg_lower)
    if equipment_name:
        extracted["equipment_name"] = equipment_name
        entities.append(ExtractedEntity(field="equipment_name", value=equipment_name))
        confidence += 0.35
    else:
        equipment_name = _extract_equipment_name_fallback(msg_lower)
        if equipment_name:
            extracted["equipment_name"] = equipment_name
            entities.append(ExtractedEntity(field="equipment_name", value=equipment_name))
            confidence += 0.2

    hours_used = _extract_hours_used(msg_lower)
    if hours_used is not None:
        extracted["hours_used"] = hours_used
        entities.append(ExtractedEntity(field="hours_used", value=hours_used))
        confidence += 0.3

    operator = _extract_operator(message)
    if operator:
        extracted["operator"] = operator
        entities.append(ExtractedEntity(field="operator", value=operator))
        confidence += 0.2

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

    confidence = min(confidence, 1.0)
    confidence = round(confidence, 2)

    return extracted, entities, confidence


def _extract_equipment_name(msg_lower: str) -> str | None:
    for equip_name in ["jcb", "crane", "excavator", "mixer", "roller", "drill"]:
        if equip_name in msg_lower:
            return equip_name

    if "drill machine" in msg_lower:
        return "drill machine"

    return None


def _extract_equipment_name_fallback(msg_lower: str) -> str | None:
    words = msg_lower.split()
    for word in words:
        result = lookup_equipment(word)
        if result:
            return result
    return None


def _extract_hours_used(msg_lower: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)\s*(?:worked|used|of work)?",
        r"(?:worked|used|operated|for)\s*(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|h)",
        r"(\d+(?:\.\d+)?)\s*(?:hrs?)\s*(?:shift)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return float(match.group(1))
    return None


def _extract_operator(message: str) -> str | None:
    patterns = [
        r"(?:by|operator|operated\s*by|driven\s*by|manned\s*by)\s+([A-Za-z\s]+?)(?:\s+(?:on|for|at|floor|and|\.)|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if 2 < len(candidate) < 40:
                return candidate
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
        "excavation", "earthwork", "levelling", "compaction",
    ]
    for activity in activity_keywords:
        if activity in msg_lower:
            return activity
    return None
