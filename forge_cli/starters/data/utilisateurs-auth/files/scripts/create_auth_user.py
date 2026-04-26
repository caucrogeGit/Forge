from core.database.connection import close_connection, get_connection
from core.security.hashing import hacher_mot_de_passe


LOGIN = "admin"
PASSWORD = "secret123"


def main() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO utilisateur (Login, Prenom, Nom, Email, PasswordHash, Actif)
            VALUES (?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                Prenom = VALUES(Prenom),
                Nom = VALUES(Nom),
                Email = VALUES(Email),
                PasswordHash = VALUES(PasswordHash),
                Actif = VALUES(Actif)
            """,
            (
                LOGIN,
                "Ada",
                "Lovelace",
                "admin@example.test",
                hacher_mot_de_passe(PASSWORD),
                True,
            ),
        )
        connection.commit()
    finally:
        cursor.close()
        close_connection(connection)

    print("Utilisateur de test prêt :")
    print(f"  login    {LOGIN}")
    print(f"  password {PASSWORD}")


if __name__ == "__main__":
    main()
