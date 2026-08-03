# pyright: strict
"""core/http/health.py — Sonde de disponibilité `GET /health`.

Ticket : CORE-WSGI-HEALTH-PARITY-001.

`GET /health` → `200 {"status": "ok"}` figure au contrat de stabilité
(`docs/release/stability-contract.md`) comme surface publique garantie.

Elle n'était pourtant servie que par le serveur de développement, qui la
traitait par un littéral inscrit dans le `do_GET` du squelette. Le chemin WSGI,
seul chemin de production supporté, ne la connaissait pas et répondait 404. Un
opérateur qui branchait la sonde de son superviseur sur `/health` derrière
Gunicorn obtenait une application déclarée morte alors qu'elle servait.

Les deux tests de la sonde passaient, parce que tous deux exerçaient le serveur
de développement, l'un en appelant `do_GET`, l'autre en lançant `python app.py`.

Ce module est la cause retirée (règle A) : la réponse est définie **une fois**,
et les deux serveurs la servent. Un futur écart de contenu entre les deux
chemins devient impossible, puisqu'il n'y a plus deux contenus.

Périmètre volontairement nul :
- la sonde ne touche pas la base, ne compte rien, n'authentifie personne ;
- elle répond que le processus est vivant et sait construire une réponse.

Une sonde qui interroge la base transforme une base lente en application
déclarée morte, et fait redémarrer par le superviseur le seul composant qui
allait bien.
"""
from __future__ import annotations

from core.http.response import Response

#: Chemin de la sonde, tel qu'écrit au contrat de stabilité.
HEALTH_PATH = "/health"

#: Corps exact garanti par le contrat.
HEALTH_BODY = b'{"status": "ok"}'


def is_health_request(path: str) -> bool:
    """Dit si `path` vise la sonde.

    Compare le chemin seul. L'appelant passe `request.path`, déjà débarrassé de
    la chaîne de requête.
    """
    return path == HEALTH_PATH


def health_response() -> Response:
    """Retourne la réponse de disponibilité, identique sur les deux serveurs."""
    return Response(200, HEALTH_BODY, "application/json")
