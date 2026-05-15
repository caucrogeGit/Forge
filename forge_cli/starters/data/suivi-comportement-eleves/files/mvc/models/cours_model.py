from core.database.db import fetch_all, fetch_one

SELECT_COURS = """
SELECT Id, DateCours, Titre, Classe
FROM cours
ORDER BY DateCours DESC, Id DESC
"""

SELECT_COURS_BY_ID = """
SELECT Id, DateCours, Titre, Classe
FROM cours
WHERE Id = ?
LIMIT 1
"""

SELECT_COURS_RECENTS = """
SELECT Id, DateCours, Titre, Classe
FROM cours
ORDER BY DateCours DESC, Id DESC
LIMIT ?
"""


def get_cours() -> list[dict]:
    return fetch_all(SELECT_COURS)


def get_cours_by_id(cours_id: int) -> dict | None:
    return fetch_one(SELECT_COURS_BY_ID, (cours_id,))


def get_cours_recents(limit: int = 5) -> list[dict]:
    return fetch_all(SELECT_COURS_RECENTS, (limit,))
