# pyright: strict
"""
core/database/backend.py — Contrat de backend BDD et résolveur (ADR-054)
========================================================================
Le cœur de Forge est agnostique BDD : il ne connaît pas de SGBD particulier,
il connaît un *contrat* de backend. Chaque SGBD est fourni par un opt-in
(`forge-mvc-mariadb`, `forge-mvc-sqlite`, ...) qui implémente ce contrat et
s'enregistre via un entry point de packaging, dans le groupe
``forge_mvc.db_backend``.

    [project.entry-points."forge_mvc.db_backend"]
    mariadb = "forge_mvc_mariadb.backend:MariaDBBackend"

Le résolveur découvre le backend installé sans configuration : l'application
« voit » l'opt-in et se câble dessus. Règles (ADR-054) :

- un seul backend autorisé par projet (exclusivité mutuelle) ;
- aucun backend installé → erreur explicite (le cœur n'a aucune prise en charge
  BDD par lui-même : il faut installer un opt-in, par exemple forge-mvc-mariadb) ;
- la variable d'environnement ``DB_BACKEND`` tranche un cas ambigu en nommant
  explicitement le backend voulu (par son nom d'entry point).

Un backend doit fournir des connexions compatibles avec l'API d'exécution du
cœur (`core.database.db`) : objets exposant ``cursor(dictionary=...)``,
``commit()``, ``rollback()``, ``close()``, l'attribut ``autocommit`` et, sur le
curseur, ``execute``, ``fetchone``, ``fetchall``, ``lastrowid``, ``rowcount``.
"""
import logging
import os
import threading
from importlib.metadata import entry_points
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "forge_mvc.db_backend"
ENV_OVERRIDE = "DB_BACKEND"


@runtime_checkable
class DatabaseBackend(Protocol):
    """Contrat qu'un opt-in de backend BDD doit implémenter."""

    name: str

    def get_connection(self) -> Any:
        """Fournit une connexion prête à l'emploi (pool ou directe)."""
        ...

    def close_connection(self, connection: Any) -> None:
        """Restitue/ferme la connexion empruntée."""
        ...


_backend: "DatabaseBackend | None" = None
_lock = threading.Lock()


def _no_backend_error() -> "RuntimeError":
    return RuntimeError(
        "Aucun backend BDD installé. Le cœur de Forge est agnostique BDD "
        "(ADR-054) : installez un opt-in de backend, par exemple "
        "`pip install forge-mvc-mariadb`."
    )


def _discover() -> "DatabaseBackend":
    discovered = list(entry_points(group=ENTRY_POINT_GROUP))

    requested = os.environ.get(ENV_OVERRIDE)
    if requested:
        matches = [ep for ep in discovered if ep.name == requested]
        if not matches:
            available = ", ".join(sorted(ep.name for ep in discovered)) or "aucun"
            raise RuntimeError(
                f"Backend BDD demandé introuvable : {requested!r} "
                f"(DB_BACKEND). Backends installés : {available}."
            )
        return matches[0].load()()

    if len(discovered) > 1:
        names = ", ".join(sorted(ep.name for ep in discovered))
        raise RuntimeError(
            f"Plusieurs backends BDD installés ({names}). Un seul est autorisé "
            "par projet (ADR-054). Désinstallez les opt-ins en trop ou fixez "
            "DB_BACKEND."
        )

    if len(discovered) == 1:
        backend = discovered[0].load()()
        logger.debug("Backend BDD résolu via entry point : %s", discovered[0].name)
        return backend

    raise _no_backend_error()


def get_backend() -> "DatabaseBackend":
    """Retourne le backend BDD actif (résolu une fois, mémorisé)."""
    global _backend
    if _backend is None:
        with _lock:
            if _backend is None:
                _backend = _discover()
    return _backend


def reset_backend() -> None:
    """Réinitialise le backend résolu.

    Ferme proprement le backend courant s'il expose ``close()`` (libération
    du pool), puis force une nouvelle résolution au prochain ``get_backend()``.
    Utilisé en fin de session de test.
    """
    global _backend
    with _lock:
        if _backend is not None:
            close = getattr(_backend, "close", None)
            if callable(close):
                close()
        _backend = None
