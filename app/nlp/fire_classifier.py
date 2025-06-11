import unicodedata

# Rozbudowana lista słów kluczowych powiązanych z pożarami
KEYWORDS = [
    # 🇺🇸 English
    "fire", "wildfire", "forest fire", "bushfire", "house fire", "grass fire",
    "burning", "flames", "blaze", "inferno", "smoke", "evacuation", "evacuated",
    "firestorm", "heatwave", "heat wave", "firefighters", "first responders",
    "fire spread", "flaming", "ignited", "scorched", "charred", "sparked", "explosion",
    "wild fire", "wild-fire", "forest-fire", "fire emergency", "fire danger", "wildfires",

    # 🇵🇱 Polish
    "pożar", "pozar", "pali się", "płonie", "ogień", "ognisko", "dym", "zadymienie",
    "ewakuacja", "straż pożarna", "straz pozarna", "gaszenie", "pożar lasu",
    "płonący", "spłonął", "spłonęła", "pozar lasu", "pozar budynku", "pozar mieszkania",

    # 🇫🇷 French
    "incendie", "feu", "fumée", "évacuation", "brûler",

    # 🇪🇸 Spanish
    "incendio", "fuego", "humo", "evacuación", "arder",

    # 🇩🇪 German
    "brand", "feuer", "rauch", "evakuierung", "verbrennung",

    # 🇵🇹 Portuguese
    "incêndio", "fogo", "fumaça", "evacuação",

    # 🇮🇹 Italian
    "incendio", "fuoco", "fumo", "evacuazione", "bruciare",

    # Emoji / symbole
    "🔥", "🚒", "🌲🔥"
]


def normalize_text(text: str) -> str:
    """
    Usuwa znaki diakrytyczne (np. ą -> a) i zamienia tekst na małe litery.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )


def is_fire_related(text: str) -> bool:
    """
    Sprawdza, czy dany tekst zawiera którekolwiek ze słów kluczowych związanych z pożarem.
    """
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in KEYWORDS)
