#!/usr/bin/env python
"""Czyści dane aplikacji SocialMedia z bazy PostgreSQL/SQLite.

Domyślnie usuwa wszystkie posty i wszystkich użytkowników poza kontem Admin.
Aby usunąć również Admina, użyj flagi --delete-admin.
"""

import argparse
import os
import sys
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def build_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return database_url

    pg_user = os.getenv("POSTGRES_USER")
    pg_password = os.getenv("POSTGRES_PASSWORD")
    pg_host = os.getenv("POSTGRES_HOST")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB")

    if all([pg_user, pg_password, pg_host, pg_db]):
        encoded_password = quote_plus(pg_password)
        return f"postgresql+psycopg://{pg_user}:{encoded_password}@{pg_host}:{pg_port}/{pg_db}?sslmode=require"

    return "sqlite:///users.db"


def clear_database(delete_admin: bool, force: bool) -> int:
    if not force:
        print("[STOP] Operacja przerwana: dodaj --force aby potwierdzić czyszczenie bazy.")
        return 1

    engine = create_engine(build_database_uri())

    with engine.begin() as connection:
        post_count = connection.execute(text("SELECT COUNT(*) FROM post")).scalar_one()
        user_count = connection.execute(text('SELECT COUNT(*) FROM "user"')).scalar_one()

        connection.execute(text("DELETE FROM post"))

        if delete_admin:
            connection.execute(text('DELETE FROM "user"'))
        else:
            connection.execute(text('DELETE FROM "user" WHERE username <> :admin_name'), {"admin_name": "Admin"})

        remaining_users = connection.execute(text('SELECT COUNT(*) FROM "user"')).scalar_one()

    print("[OK] Baza wyczyszczona.")
    print(f"- Usunięte posty: {post_count}")
    print(f"- Użytkownicy przed czyszczeniem: {user_count}")
    if delete_admin:
        print("- Konto Admin również usunięte")
    else:
        print("- Konto Admin zostało zachowane (jeśli istniało)")
    print(f"- Użytkownicy po czyszczeniu: {remaining_users}")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Czyści dane aplikacji z bazy danych")
    parser.add_argument("--delete-admin", action="store_true", help="Usuń także użytkownika Admin")
    parser.add_argument("--force", action="store_true", help="Wymagane potwierdzenie operacji")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    sys.exit(clear_database(delete_admin=arguments.delete_admin, force=arguments.force))
