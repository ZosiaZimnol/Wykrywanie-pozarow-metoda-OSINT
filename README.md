JAK URUCHOMIĆ? 

1. Sklonuj repozytorium:
git clone https://github.com/TwojaNazwa/Wykrywanie-pozarow-metoda-OSINT.git
cd Wykrywanie-pozarow-metoda-OSINT

 2.Uruchom projekt (Docker Compose):
docker compose up --build

3. Uruchom frontend
cd frontend
python -m http.server 8080

4. Otwórz w przeglądarce:

Usługa			Adres

Backend (FastAPI)	http://localhost:8000/docs
Frontend (React)	http://localhost:3000
PgAdmin			http://localhost:5050
