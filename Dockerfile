FROM python:3.11-slim

# Środowisko
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Systemowe zależności (np. dla psycopg2)
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    apt-get clean

# Katalog roboczy
WORKDIR /app

# Plik zależności
COPY requirements.txt /app/

# Instalacja bibliotek
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Instalacja modelu spaCy (PO zainstalowaniu spacy)
RUN python -m spacy download en_core_web_sm

# Kopiowanie aplikacji
COPY . /app

# Port
EXPOSE 8000

# Uruchamianie aplikacji
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]