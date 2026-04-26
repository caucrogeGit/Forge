import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    APP_ENV,
    APP_NAME,
    DB_APP_HOST,
    DB_APP_LOGIN,
    DB_APP_PORT,
    DB_APP_PWD,
    DB_NAME,
    DB_POOL_SIZE,
    SQL_DIR,
    UPLOAD_ALLOWED_EXTENSIONS,
    UPLOAD_ALLOWED_MIME_TYPES,
    UPLOAD_MAX_SIZE,
    UPLOAD_ROOT,
    VIEWS_DIR,
)
from core.database.connection import close_connection, get_connection
import core.forge as forge


VILLES = [
    ("Dreux", "28100"),
    ("Chartres", "28000"),
    ("Paris", "75000"),
    ("Lyon", "69000"),
    ("Nantes", "44000"),
]

forge.configure(
    app_name=APP_NAME,
    app_env=APP_ENV,
    views_dir=VIEWS_DIR,
    sql_dir=SQL_DIR,
    upload_root=UPLOAD_ROOT,
    upload_max_size=UPLOAD_MAX_SIZE,
    upload_allowed_extensions=UPLOAD_ALLOWED_EXTENSIONS,
    upload_allowed_mime_types=UPLOAD_ALLOWED_MIME_TYPES,
    db_host=DB_APP_HOST,
    db_port=DB_APP_PORT,
    db_name=DB_NAME,
    db_user=DB_APP_LOGIN,
    db_password=DB_APP_PWD,
    db_pool_size=DB_POOL_SIZE,
)


def main() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    created = 0
    try:
        for nom, code_postal in VILLES:
            cursor.execute(
                "SELECT VilleId FROM ville WHERE Nom = ? AND CodePostal = ? LIMIT 1",
                (nom, code_postal),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                "INSERT INTO ville (Nom, CodePostal) VALUES (?, ?)",
                (nom, code_postal),
            )
            created += 1
        connection.commit()
    finally:
        cursor.close()
        close_connection(connection)

    print("Villes de test prêtes :")
    for nom, code_postal in VILLES:
        print(f"  {nom} {code_postal}")
    print(f"{created} ville(s) ajoutée(s).")


if __name__ == "__main__":
    main()
