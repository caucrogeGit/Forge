from core.database.db import fetch_all, fetch_one

SELECT_ELEVES = """
SELECT Id, Nom, Prenom, Classe, Actif
FROM eleve
ORDER BY Classe, Nom, Prenom
"""

SELECT_ELEVE_BY_ID = """
SELECT Id, Nom, Prenom, Classe, Actif
FROM eleve
WHERE Id = ?
LIMIT 1
"""


def get_eleves() -> list[dict]:
    return fetch_all(SELECT_ELEVES)


def get_eleves_actifs() -> list[dict]:
    return fetch_all(SELECT_ELEVES.replace("FROM eleve", "FROM eleve WHERE Actif = 1"))


def get_eleve_by_id(eleve_id: int) -> dict | None:
    return fetch_one(SELECT_ELEVE_BY_ID, (eleve_id,))
