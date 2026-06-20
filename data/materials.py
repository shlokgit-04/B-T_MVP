MATERIAL_DICT = {
    "cement": ["cement", "cement bags", "opc", "ppc"],
    "steel": ["steel", "tmt", "tmt bars", "rebar", "rebars", "sariya"],
    "sand": ["sand", "m-sand", "river sand", "fine aggregate"],
    "bricks": ["bricks", "brick", "red brick", "fly ash brick", "aac block"],
    "epoxy": ["epoxy", "epoxy resin", "epoxy coat"],
    "concrete": ["concrete", "ready mix", "rmc", "ready-mix"],
    "aggregate": ["aggregate", "coarse aggregate", "grit", "stone chips"],
    "grout": ["grout", "grouting material", "non-shrink grout"],
}

BRAND_DICT = {
    "ultratech": ["ultratech", "ultra tech"],
    "birla": ["birla", "birla gold", "birla super"],
    "acc": ["acc", "acc cement"],
    "ambuja": ["ambuja", "ambuja cement"],
    "jsw": ["jsw", "jsw steel"],
    "tata": ["tata", "tata steel", "tata tiscon"],
}

UNIT_ALIASES = {
    "kg": ["kg", "kgs", "kilogram", "kilograms", "kilo", "kilos"],
    "ton": ["ton", "tons", "tonne", "tonnes", "mt", "metric ton"],
    "bag": ["bag", "bags", "sack", "sacks"],
    "cubic_m": ["cubic meter", "cubic meters", "cum", "m3", "cu m"],
    "cubic_ft": ["cubic feet", "cft", "cu ft", "cubic foot"],
    "litre": ["litre", "litres", "liter", "liters", "ltr", "ltrs"],
    "piece": ["piece", "pieces", "pc", "pcs", "nos", "number", "numbers"],
    "sq_ft": ["sq ft", "sqft", "square feet", "square foot", "sft"],
    "sq_m": ["sq m", "sqm", "square meter", "square meters"],
}

MATERIAL_REQUIRED_FIELDS = [
    "project",
    "material_name",
    "quantity",
    "unit",
    "supplier",
    "rate",
    "floor",
    "activity",
]

MATERIAL_QUESTIONS = {
    "project": "Which project is this for?",
    "material_name": "What material is this?",
    "quantity": "What is the quantity?",
    "unit": "What is the unit of measurement?",
    "supplier": "Who is the supplier?",
    "rate": "What is the rate per unit?",
    "floor": "Which floor is this for?",
    "activity": "What activity is this for?",
}


def normalize_unit(raw: str) -> str | None:
    raw_lower = raw.strip().lower()
    for canonical, aliases in UNIT_ALIASES.items():
        if raw_lower == canonical or raw_lower in aliases:
            return canonical
    return None


def lookup_material(token: str) -> str | None:
    tl = token.strip().lower()
    for material, keywords in MATERIAL_DICT.items():
        if tl == material or tl in keywords:
            return material
    return None


def lookup_brand(token: str) -> str | None:
    tl = token.strip().lower()
    for brand, keywords in BRAND_DICT.items():
        if tl == brand or tl in keywords:
            return brand
    return None
