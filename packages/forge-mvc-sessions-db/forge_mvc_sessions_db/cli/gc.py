# pyright: strict
"""Commande ``forge sessions:gc`` — purge des sessions expirées (retour terrain 016 F35).

Appelle ``DbSessionStore.cleanup_expired()`` sur le backend BDD actif. À
brancher sur un ordonnanceur externe (cron, systemd timer) : Forge ne fournit
pas de planificateur, cette commande est le point d'entrée à déclencher.
"""
from __future__ import annotations

STATUS_OK = "[OK]"

__all__ = ["STATUS_OK", "main"]


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge sessions:gc``."""
    from forge_mvc_sessions_db.store import DbSessionStore

    removed = DbSessionStore().cleanup_expired()
    print(f"{STATUS_OK} {removed} session(s) expirée(s) purgée(s).")
    return 0
