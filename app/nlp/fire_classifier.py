import unicodedata
import re

# Subreddity do monitorowania
SUBREDDIT_NAMES = [
    "news", "Polska", "krakow", "CatastrophicFailure",  "worldnews", "Firefighting", "fire", 
    "California", "Australia", "canada", "climate", "nasikatok", "warszawa", "libek", "Rzeszow",
    "ClimateActionPlan", "Environmentalism", "bushfires", "ForestFires", "wildfire",
    "wildfiresmoke", "Firefighting", "fire", "disaster", "emergency", "naturaldisasters", "Poznan",
    "Pikabu", "OdesaUkraine", "vPlovdiv", "redmond", "pics", "geography", "BGNES"
]

# 🔥 Lista słów kluczowych
FIRE_KEYWORDS = [
    "fire", "wildfire", "forest fire", "smoke", "evacuation", "burning", "blaze", "flames",
    "bushfire", "campfire", "arson", "firefighters", "firestorm", "red flag warning", "controlled burn",
    "containment", "flare-up", "fireline", "heatwave", "scorched", "incendiary",
    # PL
    "pożar", "pożary", "dym", "płomienie", "ewakuacja", "pali się", "strażacy", "ogień",
    # ES
    "incendio", "incendios", "evacuación", "humo", "llamas", "bomberos",
    # FR
    "incendie", "feu", "fumée", "évacuation", "pompiers",
    # DE
    "brand", "waldbrand", "rauch", "evakuierung", "feuerwehr", "flammen",
    # RU
    "пожар", "горит", "эвакуация", "дым", "огонь", "пожарные",
    # IT
    "incendio", "fiamme", "evacuazione", "fumo", "vigili del fuoco",

     # Emoji / symbole
    "🔥", "🚒", "🌲🔥"
]

CUSTOM_REGION_ALIASES = {
    "Mazowieckie": "Mazowieckie", "Małopolskie": "Małopolskie", "Wielkopolskie": "Wielkopolskie",
    "Śląskie": "Śląskie", "Dolnośląskie": "Dolnośląskie", "Pomorskie": "Pomorskie",
    "Zachodniopomorskie": "Zachodniopomorskie", "Łódzkie": "Łódzkie", "Lubelskie": "Lubelskie",
    "Podkarpackie": "Podkarpackie", "Podlaskie": "Podlaskie", "Kujawsko-Pomorskie": "Kujawsko-Pomorskie",
    "Opolskie": "Opolskie", "Świętokrzyskie": "Świętokrzyskie", "Warmińsko-Mazurskie": "Warmińsko-Mazurskie",
    "Warszawa": "Warsaw", "Kraków": "Krakow", "Wrocław": "Wroclaw", "Łódź": "Lodz",
    "Poznań": "Poznan", "Gdańsk": "Gdansk", "Szczecin": "Szczecin", "Rzeszów": "Rzeszow",
    "CA": "California", "NY": "New York", "TX": "Texas", "Nev.": "Nevada", "NV": "Nevada",
    "FL": "Florida", "IL": "Illinois", "LA": "Los Angeles", "SF": "San Francisco",
    "DC": "Washington, D.C.", "WA": "Washington", "AZ": "Arizona", "UK": "United Kingdom",
    "DE": "Germany", "FR": "France", "PL": "Poland", "ES": "Spain", "UA": "Ukraine",
    "CZ": "Czech Republic", "RU": "Russia", "IN": "India", "CN": "China"
}

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
    Dopasowuje całe słowa oraz frazy, a nie substringi.
    """
    normalized = normalize_text(text)

    # Budujemy pattern dla fraz i słów kluczowych - escape żeby uwzględnić np. znaki specjalne
    # Posortuj FIRE_KEYWORDS po długości malejąco, by frazy były sprawdzane najpierw
    sorted_keywords = sorted(FIRE_KEYWORDS, key=len, reverse=True)
    pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in sorted_keywords) + r')\b'

    # Szukamy dopasowania całych słów / fraz
    return re.search(pattern, normalized) is not None