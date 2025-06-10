KEYWORDS = ["fire", "wildfire", "blaze", "evacuation", "forest fire", "smoke", "burning"]

def is_fire_related(text: str) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in KEYWORDS)