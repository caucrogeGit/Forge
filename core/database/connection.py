# pyright: strict
"""
core/database/connection.py — Emprunt de connexion BDD (API interne)
=====================================================================
Ce module est une API interne. Pour le code applicatif, utiliser plutôt
`core.database.db` qui fournit `fetch_one`, `fetch_all`, `execute`, `insert`.

Les fonctions de ce module sont à utiliser uniquement pour :
- transactions multi-statement (via `core.database.transaction`)
- opérations en bulk avec optimisations spécifiques
- scripts d'administration

Pour tout le reste, utiliser `core.database.db`.

---

Depuis ADR-054, le cœur est agnostique BDD : ce module ne connaît plus de SGBD.
Il délègue l'acquisition et la restitution des connexions au backend actif,
résolu par `core.database.backend.get_backend()` (opt-in installé, ou repli
MariaDB intégré tant que l'extraction n'est pas faite).

Chaque requête HTTP emprunte une connexion et la restitue à l'appel de
`close_connection()`. Selon le backend, la connexion retourne à un pool
plutôt que d'être détruite.
"""
from typing import Any

from core.database.backend import get_backend


def get_connection() -> Any:
    """Emprunte une connexion auprès du backend BDD actif."""
    return get_backend().get_connection()


def close_connection(connection: Any) -> None:
    """Restitue la connexion au backend BDD actif."""
    get_backend().close_connection(connection)
