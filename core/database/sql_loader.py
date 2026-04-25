"""
core/sql_loader.py — Chargeur dynamique de modules SQL
=======================================================
Les sous-dossiers sql/dev/ et sql/prod/ ne sont pas des packages Python
valides comme noms d'import direct depuis la racine du projet.
Ce module utilise importlib pour charger le bon fichier selon APP_ENV.

Usage dans un modèle :
    from core.sql_loader import charger_queries
    q = charger_queries("client_queries.py")
    cursor.execute(q.COUNT_CLIENTS)

Dossiers chargés selon APP_ENV :
    dev  → sql/dev/
    prod → sql/prod/

Cache thread-safe :
    Les modules SQL sont mis en cache après le premier chargement.
    Le cache est invalidé automatiquement si mtime_ns ou size change.
"""
import importlib.util
import os
import threading

from core.forge import get as _cfg

_lock:  threading.RLock = threading.RLock()
_cache: dict[str, dict] = {}


def charger_queries(nom_fichier: str):
    """
    Charge et retourne un module de requêtes SQL depuis {SQL_DIR}/{APP_ENV}/.

    Le module est mis en cache et réutilisé tant que le fichier n'a pas changé.

    Args :
        nom_fichier (str) : nom du fichier — ex: "client_queries.py"

    Returns :
        module Python avec les constantes SQL (COUNT_CLIENTS, ADD_CLIENT…)

    Raises :
        FileNotFoundError : si le fichier est absent du dossier d'environnement
    """
    chemin = os.path.join(_cfg("sql_dir"), _cfg("app_env"), nom_fichier)

    if not os.path.exists(chemin):
        sql_dir = _cfg("sql_dir")
        app_env = _cfg("app_env")
        raise FileNotFoundError(
            f"Fichier SQL introuvable : {chemin}\n"
            f"Copier {sql_dir}/example/{nom_fichier} dans {sql_dir}/{app_env}/ et compléter."
        )

    chemin = os.path.realpath(chemin)
    stat   = os.stat(chemin)

    with _lock:
        entry = _cache.get(chemin)
        if entry and entry["mtime_ns"] == stat.st_mtime_ns and entry["size"] == stat.st_size:
            return entry["module"]

        spec   = importlib.util.spec_from_file_location(nom_fichier[:-3], chemin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _cache[chemin] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size, "module": module}
        return module


def _vider_cache() -> None:
    """Vide intégralement le cache — usage réservé aux tests."""
    with _lock:
        _cache.clear()
