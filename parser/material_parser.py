from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from data.materials import lookup_brand, lookup_material, normalize_unit
from models.schemas import ExtractedEntity


def parse_material(message: str) -> Tuple[Dict[str, Any], List[ExtractedEntity], float]:
    extracted: Dict[str, Any] = {}
    entities: List[ExtractedEntity] = []
    confidence = 0.0

    msg_lower = message.strip().lower()

    material_name = _extract_material_name(msg_lower, message)
    if material_name:
        extracted["material_name"] = material_name
        entities.append(ExtractedEntity(field="material_name", value=material_name))
        confidence += 0.3
    else:
        material_name = _extract_material_name_fallback(msg_lower)
        if material_name:
            extracted["material_name"] = material_name
            entities.append(ExtractedEntity(field="material_name", value=material_name))
            confidence += 0.2

    brand = _extract_brand(msg_lower)
    if brand:
        extracted["brand"] = brand
        entities.append(ExtractedEntity(field="brand", value=brand))
        confidence += 0.1

    quantity, unit = _extract_quantity_unit(msg_lower)
    if quantity is not None:
        extracted["quantity"] = quantity
        entities.append(ExtractedEntity(field="quantity", value=quantity))
        confidence += 0.3
    if unit:
        extracted["unit"] = unit
        entities.append(ExtractedEntity(field="unit", value=unit))
        confidence += 0.1

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

    supplier = _extract_supplier(message)
    if supplier:
        extracted["supplier"] = supplier
        entities.append(ExtractedEntity(field="supplier", value=supplier))
        confidence += 0.15

    rate = _extract_rate(msg_lower)
    if rate is not None:
        extracted["rate"] = rate
        entities.append(ExtractedEntity(field="rate", value=rate))
        confidence += 0.2

    confidence = min(confidence, 1.0)
    confidence = round(confidence, 2)

    return extracted, entities, confidence


def _extract_material_name(msg_lower: str, original: str) -> str | None:
    for material_name in [
        "cement", "steel", "sand", "bricks", "epoxy",
        "concrete", "aggregate", "grout",
    ]:
        if material_name in msg_lower:
            return material_name

    for _, keywords in [
        ("cement", ["opc", "ppc", "cement bags"]),
        ("steel", ["tmt", "tmt bars", "rebar", "rebars", "sariya"]),
        ("sand", ["m-sand", "river sand", "fine aggregate"]),
        ("bricks", ["red brick", "fly ash brick", "aac block"]),
        ("concrete", ["ready mix", "rmc", "ready-mix"]),
        ("aggregate", ["coarse aggregate", "grit", "stone chips"]),
        ("grout", ["grouting material", "non-shrink grout"]),
    ]:
        for kw in keywords:
            if kw in msg_lower:
                return material_name

    return None


def _extract_material_name_fallback(msg_lower: str) -> str | None:
    words = msg_lower.split()
    for word in words:
        result = lookup_material(word)
        if result:
            return result
    return None


def _extract_brand(msg_lower: str) -> str | None:
    for brand in ["ultratech", "birla", "acc", "ambuja", "jsw", "tata"]:
        if brand in msg_lower:
            return brand

    for brand_key in ["ultra tech", "birla gold", "birla super", "tata tiscon"]:
        if brand_key in msg_lower:
            return brand_key.split()[0]

    return None


def _extract_quantity_unit(msg_lower: str) -> Tuple[float | None, str | None]:
    patterns = [
        (r"(\d+)\s*(?:kg|kgs|kilogram|kilograms|kilo|kilos)", "kg"),
        (r"(\d+)\s*(?:ton|tons|tonne|tonnes|mt|metric\s*ton)", "ton"),
        (r"(\d+)\s*(?:bag|bags|sack|sacks)", "bag"),
        (r"(\d+)\s*(?:cubic\s*meter|cubic\s*meters|cum|m3|cu\s*m)", "cubic_m"),
        (r"(\d+)\s*(?:cubic\s*feet|cft|cu\s*ft|cubic\s*foot)", "cubic_ft"),
        (r"(\d+)\s*(?:litre|litres|liter|liters|ltr|ltrs)", "litre"),
        (r"(\d+)\s*(?:piece|pieces|pc|pcs|nos|number|numbers)", "piece"),
        (r"(\d+)\s*(?:sq\s*ft|sqft|square\s*feet|sft)", "sq_ft"),
        (r"(\d+)\s*(?:sq\s*m|sqm|square\s*meter|square\s*meters)", "sq_m"),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return float(match.group(1)), unit

    number_match = re.search(r"(\d+)", msg_lower)
    if number_match:
        return float(number_match.group(1)), None

    return None, None


def _extract_project(message: str) -> str | None:
    project_patterns = [
        r"(?:for|at|project)\s+([A-Za-z0-9\s]+?)(?:\s+(?:floor|building|tower|phase|supplier|rate|activity|and|for)\b|$)",
        r"([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)\s+(?:tower|building|project)",
    ]

    for pattern in project_patterns:
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


def _extract_supplier(message: str) -> str | None:
    patterns = [
        r"(?:from|supplier|supplied\s*by|vendor|company)\s+([A-Za-z0-9\s&]+?)(?:\s+(?:for|rate|at|price|floor|activity|and|\.)|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if 2 < len(candidate) < 50:
                return candidate
    return None


def _extract_rate(msg_lower: str) -> float | None:
    rate_patterns = [
        r"(?:rate|price|@|at)\s*(?:is\s*)?(?:rs|inr|₹)?\s*(\d+(?:[,.]\d+)?)\s*(?:per|/|each)?",
        r"(?:rs|inr|₹)\s*(\d+(?:[,.]\d+)?)\s*(?:per|/|each)?",
        r"@\s*(\d+(?:[,.]\d+)?)",
    ]

    for pattern in rate_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            raw = match.group(1).replace(",", "")
            return float(raw)
    return None
