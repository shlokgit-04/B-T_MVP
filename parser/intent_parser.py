from __future__ import annotations

import re
from typing import Optional, Tuple

from data.equipment import EQUIPMENT_DICT
from data.labour_types import LABOUR_DICT
from data.materials import MATERIAL_DICT


def detect_entry_type(message: str) -> Tuple[Optional[str], float]:
    if not message or not message.strip():
        return None, 0.0

    msg_lower = message.strip().lower()

    material_score = _score_material_intent(msg_lower)
    labour_score = _score_labour_intent(msg_lower)
    equipment_score = _score_equipment_intent(msg_lower)

    scores = [
        ("material", material_score),
        ("labour", labour_score),
        ("equipment", equipment_score),
    ]

    best_type, best_score = max(scores, key=lambda x: x[1])

    if best_score <= 0:
        return None, 0.0

    normalized = min(best_score / 3.0, 1.0)
    return best_type, round(normalized, 2)


def _score_material_intent(msg: str) -> float:
    score = 0.0

    for material, keywords in MATERIAL_DICT.items():
        for kw in keywords:
            if kw in msg:
                score += 1.5
                break

    purchase_verbs = ["bought", "purchased", "ordered", "added", "received", "procured"]
    for verb in purchase_verbs:
        if verb in msg:
            score += 0.5
            break

    quantity_patterns = [
        r"\d+\s*(?:kg|kgs|ton|tons|bag|bags|cum|m3|cft|pcs|nos|litre|litres|ltr)",
        r"\d+",
    ]
    for pat in quantity_patterns:
        if re.search(pat, msg):
            score += 0.3
            break

    unit_keywords = ["kg", "kgs", "ton", "tons", "bag", "bags", "cum", "m3", "cft"]
    for unit in unit_keywords:
        if unit in msg:
            score += 0.2
            break

    if "rate" in msg or "price" in msg:
        score += 0.3

    brand_keywords = ["ultratech", "birla", "acc", "ambuja", "jsw", "tata"]
    for brand in brand_keywords:
        if brand in msg:
            score += 0.4
            break

    labour_keywords = set()
    for _, kws in LABOUR_DICT.items():
        for kw in kws:
            labour_keywords.add(kw)
    for lkw in labour_keywords:
        if lkw in msg:
            score -= 1.0
            break

    equip_keywords = set()
    for _, kws in EQUIPMENT_DICT.items():
        for kw in kws:
            equip_keywords.add(kw)
    for ekw in equip_keywords:
        if ekw in msg:
            score -= 1.0
            break

    return max(score, 0.0)


def _score_labour_intent(msg: str) -> float:
    score = 0.0

    for labour, keywords in LABOUR_DICT.items():
        for kw in keywords:
            if kw in msg:
                score += 1.5
                break

    worker_verbs = ["added", "deployed", "assigned", "worked", "hired", "on site"]
    for verb in worker_verbs:
        if verb in msg:
            score += 0.5
            break

    if re.search(r"\d+\s*(?:mason|carpenter|helper|labour|worker|fixer)", msg):
        score += 0.5

    number_words = re.findall(r"\b\d+\b", msg)
    if len(number_words) >= 1:
        score += 0.3

    if "hour" in msg or "hr" in msg or "shift" in msg or "day" in msg:
        score += 0.3

    material_keywords = set()
    for _, kws in MATERIAL_DICT.items():
        for kw in kws:
            material_keywords.add(kw)
    for mkw in material_keywords:
        if mkw in msg:
            score -= 1.0
            break

    equip_keywords = set()
    for _, kws in EQUIPMENT_DICT.items():
        for kw in kws:
            equip_keywords.add(kw)
    for ekw in equip_keywords:
        if ekw in msg:
            score -= 1.0
            break

    return max(score, 0.0)


def _score_equipment_intent(msg: str) -> float:
    score = 0.0

    for equip, keywords in EQUIPMENT_DICT.items():
        for kw in keywords:
            if kw in msg:
                score += 1.5
                break

    operation_verbs = ["worked", "used", "operated", "deployed", "running"]
    for verb in operation_verbs:
        if verb in msg:
            score += 0.5
            break

    if re.search(r"\d+\s*(?:hour|hr|shift)", msg):
        score += 0.3

    equip_operators = ["jcb", "crane", "excavator", "roller", "mixer", "drill"]
    for eop in equip_operators:
        if eop in msg:
            score += 0.3
            break

    material_keywords = set()
    for _, kws in MATERIAL_DICT.items():
        for kw in kws:
            material_keywords.add(kw)
    for mkw in material_keywords:
        if mkw in msg:
            score -= 1.0
            break

    labour_keywords = set()
    for _, kws in LABOUR_DICT.items():
        for kw in kws:
            labour_keywords.add(kw)
    for lkw in labour_keywords:
        if lkw in msg:
            score -= 1.0
            break

    return max(score, 0.0)
