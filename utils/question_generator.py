from __future__ import annotations

from typing import Dict, List, Optional

from data.equipment import EQUIPMENT_QUESTIONS
from data.labour_types import LABOUR_QUESTIONS
from data.materials import MATERIAL_QUESTIONS


QUESTIONS_MAP = {
    "material": MATERIAL_QUESTIONS,
    "labour": LABOUR_QUESTIONS,
    "equipment": EQUIPMENT_QUESTIONS,
}


def get_next_question(
    entry_type: Optional[str],
    missing_fields: List[str],
    current_data: Dict[str, object],
) -> Optional[str]:
    if entry_type not in QUESTIONS_MAP:
        return None

    questions = QUESTIONS_MAP[entry_type]

    for field in missing_fields:
        if field in questions:
            current_value = current_data.get(field)
            if current_value is None or current_value == "" or current_value == 0:
                return questions[field]

    return None


def generate_summary(
    entry_type: Optional[str],
    data: Dict[str, object],
) -> Optional[str]:
    if not entry_type:
        return None

    entry_labels = {
        "material": "Material Entry",
        "labour": "Labour Entry",
        "equipment": "Equipment Entry",
    }

    label = entry_labels.get(entry_type, entry_type.capitalize())
    lines = [f"{label} Summary", "=" * 30]

    field_labels = {
        "material": {
            "project": "Project",
            "material_name": "Material",
            "quantity": "Quantity",
            "unit": "Unit",
            "supplier": "Supplier",
            "rate": "Rate",
            "floor": "Floor",
            "activity": "Activity",
        },
        "labour": {
            "project": "Project",
            "labour_type": "Labour Type",
            "worker_count": "Workers",
            "hours": "Hours",
            "floor": "Floor",
            "activity": "Activity",
            "rate": "Rate",
        },
        "equipment": {
            "project": "Project",
            "equipment_name": "Equipment",
            "hours_used": "Hours Used",
            "operator": "Operator",
            "floor": "Floor",
            "activity": "Activity",
        },
    }

    labels = field_labels.get(entry_type, {})
    for field, label_text in labels.items():
        value = data.get(field)
        if value is not None and value != "" and value != 0:
            if field == "unit" and "quantity" in data:
                continue
            if field == "quantity" and "unit" in data:
                unit = data.get("unit", "")
                unit_label = _format_unit(unit)
                lines.append(f"{label_text}:\n  {value} {unit_label}".strip())
            else:
                lines.append(f"{label_text}:\n  {value}")

    lines.append("")
    lines.append("Confirm save? (yes / no)")

    return "\n".join(lines)


def _format_unit(unit: str) -> str:
    unit_labels = {
        "kg": "kg",
        "ton": "ton",
        "bag": "bags",
        "cubic_m": "cu.m",
        "cubic_ft": "cft",
        "litre": "L",
        "piece": "pcs",
        "sq_ft": "sq.ft",
        "sq_m": "sq.m",
    }
    return unit_labels.get(unit, unit)
