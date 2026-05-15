from core.database.db import fetch_all


SELECT_VILLES = """
SELECT VilleId, Nom, CodePostal
FROM ville
ORDER BY Nom
"""


def get_villes():
    return fetch_all(SELECT_VILLES)
