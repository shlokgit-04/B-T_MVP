from __future__ import annotations

from typing import Dict, List, Optional

from data.equipment import EQUIPMENT_REQUIRED_FIELDS
from data.labour_types import LABOUR_REQUIRED_FIELDS
from data.materials import MATERIAL_REQUIRED_FIELDS


REQUIRED_FIELDS_MAP = {
    "material": MATERIAL_REQUIRED_FIELDS,
    "labour": LABOUR_REQUIRED_FIELDS,
    "equipment": EQUIPMENT_REQUIRED_FIELDS,
}


def get_missing_fields(
    entry_type: Optional[str],
    extracted: Dict[str, object],
) -> List[str]:
    if entry_type not in REQUIRED_FIELDS_MAP:
        return []

    required = REQUIRED_FIELDS_MAP[entry_type]
    missing: List[str] = []

    for field in required:
        value = extracted.get(field)
        if value is None or value == "" or value == 0:
            missing.append(field)

    return missing


def get_progress(
    entry_type: Optional[str],
    extracted: Dict[str, object],
) -> int:
    if entry_type not in REQUIRED_FIELDS_MAP:
        return 0

    required = REQUIRED_FIELDS_MAP[entry_type]
    if not required:
        return 100

    filled = sum(
        1
        for field in required
        if extracted.get(field) is not None
        and extracted.get(field) != ""
        and extracted.get(field) != 0
    )

    return int((filled / len(required)) * 100)
