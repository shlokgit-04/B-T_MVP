LABOUR_DICT = {
    "mason": ["mason", "masons", "brick layer", "bricklayer"],
    "carpenter": ["carpenter", "carpenters", "formwork"],
    "steel fixer": ["steel fixer", "steel fixers", "bar bender", "fabricator"],
    "electrician": ["electrician", "electricians", "electrical", "wireman"],
    "plumber": ["plumber", "plumbers", "plumbing"],
    "painter": ["painter", "painters", "painting"],
    "helper": ["helper", "helpers", "labour", "labourer", "unskilled"],
}

LABOUR_REQUIRED_FIELDS = [
    "project",
    "labour_type",
    "worker_count",
    "hours",
    "floor",
    "activity",
    "rate",
]

LABOUR_QUESTIONS = {
    "project": "Which project is this for?",
    "labour_type": "What type of labour?",
    "worker_count": "How many workers?",
    "hours": "How many hours did they work?",
    "floor": "Which floor is this for?",
    "activity": "What activity is this for?",
    "rate": "What is the hourly rate?",
}


def lookup_labour(token: str) -> str | None:
    tl = token.strip().lower()
    for labour, keywords in LABOUR_DICT.items():
        if tl == labour or tl in keywords:
            return labour
    return None
