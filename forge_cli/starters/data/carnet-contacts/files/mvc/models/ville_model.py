from core.database.db import fetch_all


SELECT_VILLES = """
SELECT Id, Nom, CodePostal
FROM ville
ORDER BY Nom
"""


def get_villes():
    return fetch_all(SELECT_VILLES)
