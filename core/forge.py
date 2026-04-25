"""
core/forge.py — Registre de configuration du noyau Forge
=========================================================
Centralise les paramètres runtime du framework.
Aucun module de core ne doit importer config.py directement —
tout passe par ce registre.

Cycle de vie :
    1. app.py importe config (variables d'environnement)
    2. app.py appelle forge.configure(**kwargs)
    3. core/* lit les valeurs via forge.get(key)

Les chemins relatifs (views_dir, sql_dir) sont automatiquement
résolus en chemins absolus par rapport à la racine du projet.
"""
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_cfg = {
    # Application
    "app_name":    "Forge",
    "app_env":     "dev",
    # Vues et SQL
    "views_dir":   os.path.join(_PROJECT_ROOT, "mvc", "views"),
    "sql_dir":     os.path.join(_PROJECT_ROOT, "mvc", "models", "sql"),
    # Uploads
    "upload_root": os.path.join(_PROJECT_ROOT, "storage", "uploads"),
    "upload_max_size": 5 * 1024 * 1024,
    "upload_allowed_extensions": ["jpg", "jpeg", "png", "webp", "pdf"],
    "upload_allowed_mime_types": [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    ],
    # Base de données
    "db_host":     "localhost",
    "db_port":     3306,
    "db_name":     "forge_db",
    "db_user":     "root",
    "db_password": "",
    "db_pool_size": 5,
    # Classes CSS utilisées par les helpers du framework (pagination…)
    # Modifiables via forge.configure(css_visible="visible", css_hidden="invisible")
    "css_visible": "block",
    "css_hidden":  "hidden",
    # Routeur actif, renseigné au démarrage pour url_for/redirect_to_route.
    "router": None,
}

_PATH_KEYS = {"views_dir", "sql_dir", "upload_root"}


def configure(**kwargs: object) -> None:
    """Configure le noyau — à appeler une fois au démarrage, avant toute requête."""
    unknown = set(kwargs) - set(_cfg)
    if unknown:
        raise KeyError(f"Clés inconnues dans forge.configure() : {unknown}")
    for key, value in kwargs.items():
        if key in _PATH_KEYS and isinstance(value, str) and not os.path.isabs(value):
            value = os.path.join(_PROJECT_ROOT, value)
        _cfg[key] = value


def get(key: str) -> object:
    """Retourne une valeur de configuration du noyau."""
    try:
        return _cfg[key]
    except KeyError:
        raise KeyError(f"Clé de configuration inconnue : {key!r}")
