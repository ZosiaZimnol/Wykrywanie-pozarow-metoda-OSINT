# Użyj lekkiego obrazu Pythona
FROM python:3.11-slim

# Zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalacja zależności systemowych potrzebnych dla psycopg2
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    apt-get clean

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie pliku z zależnościami
COPY requirements.txt /app/

# Instalacja zależności Pythona
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie całej aplikacji
COPY . /app

# Otwierany port
EXPOSE 8000

# Uruchamianie aplikacji FastAPI z uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
