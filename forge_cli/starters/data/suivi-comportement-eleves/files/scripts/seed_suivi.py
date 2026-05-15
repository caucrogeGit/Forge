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

ELEVES = [
    ("Martin",   "Alice",   "3eA"),
    ("Dupont",   "Baptiste","3eA"),
    ("Bernard",  "Chloé",   "3eA"),
    ("Leclerc",  "Damien",  "3eA"),
    ("Moreau",   "Eva",     "3eA"),
]

COURS = [
    ("2026-09-02", "Introduction au programme",   "3eA"),
    ("2026-09-09", "Chapitre 1 : Les bases",      "3eA"),
    ("2026-09-16", "Chapitre 2 : Approfondissement", "3eA"),
]

OBSERVATIONS = [
    # (eleve_index, cours_index, ne_travaille_pas, bavarde, dort, telephone, perturbe, refuse_consigne, remarque)
    (1, 0, False, True,  False, False, False, False, None),
    (1, 1, False, True,  False, True,  False, False, "A rangé le téléphone après rappel."),
    (3, 1, True,  False, True,  False, False, False, None),
    (3, 2, True,  False, False, False, True,  False, "Perturbe ses voisins."),
    (0, 2, False, False, False, False, False, True,  "Refuse de rendre le devoir."),
]


def main() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        eleve_ids = []
        for nom, prenom, classe in ELEVES:
            cursor.execute(
                """INSERT INTO eleve (Nom, Prenom, Classe, Actif)
                   VALUES (?, ?, ?, 1)
                   ON DUPLICATE KEY UPDATE Classe = VALUES(Classe), Actif = 1""",
                (nom, prenom, classe),
            )
            if cursor.lastrowid:
                eleve_ids.append(cursor.lastrowid)
            else:
                cursor.execute(
                    "SELECT Id FROM eleve WHERE Nom = ? AND Prenom = ?", (nom, prenom)
                )
                eleve_ids.append(cursor.fetchone()[0])

        cours_ids = []
        for date_cours, titre, classe in COURS:
            cursor.execute(
                """INSERT INTO cours (DateCours, Titre, Classe)
                   VALUES (?, ?, ?)
                   ON DUPLICATE KEY UPDATE Titre = VALUES(Titre)""",
                (date_cours, titre, classe),
            )
            if cursor.lastrowid:
                cours_ids.append(cursor.lastrowid)
            else:
                cursor.execute(
                    "SELECT Id FROM cours WHERE DateCours = ? AND Classe = ?", (date_cours, classe)
                )
                cours_ids.append(cursor.fetchone()[0])

        for eleve_i, cours_i, *flags_and_remarque in OBSERVATIONS:
            remarque = flags_and_remarque[-1]
            flags = flags_and_remarque[:-1]
            cursor.execute(
                """INSERT INTO observation_cours
                       (EleveId, CoursId, NeTravaillePas, Bavarde, Dort, Telephone, Perturbe, RefuseConsigne, Remarque)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON DUPLICATE KEY UPDATE
                       NeTravaillePas = VALUES(NeTravaillePas),
                       Bavarde        = VALUES(Bavarde),
                       Dort           = VALUES(Dort),
                       Telephone      = VALUES(Telephone),
                       Perturbe       = VALUES(Perturbe),
                       RefuseConsigne = VALUES(RefuseConsigne),
                       Remarque       = VALUES(Remarque)""",
                (eleve_ids[eleve_i], cours_ids[cours_i], *flags, remarque),
            )

        connection.commit()
    finally:
        cursor.close()
        close_connection(connection)

    print(f"Seed terminé : {len(ELEVES)} élèves, {len(COURS)} cours, {len(OBSERVATIONS)} observations.")


if __name__ == "__main__":
    main()
