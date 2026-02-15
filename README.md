# SocialMedia Flask API

Projekt Flask do uploadu filmów i zdjęć, generowania opisów oraz wystawiania API do integracji z n8n (Instagram, Facebook, YouTube).

## Funkcje
- Upload plików (filmy, zdjęcia) przez endpoint `/upload`
- Generowanie opisów na podstawie tekstu przez endpoint `/generate-description`
- Endpoint `/publish` do integracji z n8n (wysyłka do social media)

## Uruchomienie
1. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
2. Skonfiguruj bazę danych PostgreSQL (Neon) przez zmienne środowiskowe.

   Opcja A (zalecana):
   ```bash
   set DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```
   Aplikacja automatycznie użyje sterownika `psycopg`.

   Opcja B (alternatywnie):
   ```bash
   set POSTGRES_USER=USER
   set POSTGRES_PASSWORD=PASSWORD
   set POSTGRES_HOST=HOST
   set POSTGRES_PORT=5432
   set POSTGRES_DB=DBNAME
   ```

   Jeśli żadne zmienne nie są ustawione, aplikacja uruchomi się na lokalnym SQLite (`users.db`).

3. Uruchom serwer Flask:
   ```bash
   python app.py
   ```

## Struktura projektu
- `app.py` – główny plik aplikacji Flask
- `uploads/` – katalog na przesłane pliki
- `requirements.txt` – zależności

## Integracja z n8n
API jest gotowe do integracji z n8n. Możesz użyć HTTP Request node w n8n, aby pobrać lub wysłać dane do tego API.

## Czyszczenie bazy danych
Do wyczyszczenia danych użyj skryptu `clean_db.py`.

Zachowaj konto `Admin` (domyślnie):
```bash
python clean_db.py --force
```

Usuń wszystko łącznie z `Admin`:
```bash
python clean_db.py --delete-admin --force
```

## Uwaga
- Logika generowania opisów i integracji z social media jest wstępna i wymaga dalszego rozwoju.

## Publikacja na GitHub
Po utworzeniu pustego repozytorium na GitHub:

```bash
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TWOJ_LOGIN/TWOJE_REPO.git
git push -u origin main
```

Jeśli `origin` już istnieje, podmień adres:

```bash
git remote set-url origin https://github.com/TWOJ_LOGIN/TWOJE_REPO.git
```
