EQUIPMENT_DICT = {
    "jcb": ["jcb", "excavator", "backhoe", "loader"],
    "crane": ["crane", "mobile crane", "tower crane", "hydra"],
    "excavator": ["excavator", "hydraulic excavator", "poclain"],
    "mixer": ["mixer", "concrete mixer", "cement mixer", "mixture"],
    "roller": ["roller", "road roller", "compactor", "vibratory roller"],
    "drill machine": ["drill", "drill machine", "drilling", "rock drill"],
}

EQUIPMENT_REQUIRED_FIELDS = [
    "project",
    "equipment_name",
    "hours_used",
    "operator",
    "floor",
    "activity",
]

EQUIPMENT_QUESTIONS = {
    "project": "Which project is this for?",
    "equipment_name": "Which equipment was used?",
    "hours_used": "How many hours was it used?",
    "operator": "Who operated it?",
    "floor": "Which floor is this for?",
    "activity": "What activity is this for?",
}


def lookup_equipment(token: str) -> str | None:
    tl = token.strip().lower()
    for equip, keywords in EQUIPMENT_DICT.items():
        if tl == equip or tl in keywords:
            return equip
    return None
