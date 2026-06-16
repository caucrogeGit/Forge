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

Store de session configurable (SESSIONS-CONFIGURABLE-STORE-001) :
    forge.configure(session_store=my_store)
    Le store doit implémenter le protocole SessionStore (core.sessions.contract).
    Passer None réinitialise au MemorySessionStore par défaut.
"""
import os
from typing import Any

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_cfg = {
    # Application
    "app_name":    "Forge",
    "app_env":     "dev",
    # Vues et SQL
    "views_dir":   os.path.join(_PROJECT_ROOT, "mvc", "views"),
    "sql_dir":     os.path.join(_PROJECT_ROOT, "mvc", "models", "sql"),
    # Uploads — seul le plafond de corps multipart est du noyau (ADR-032) :
    # core/http/request.py le lit pour borner la requête, avant tout opt-in.
    # Le reste (racine de stockage, extensions/MIME autorisés, plafond pixels
    # anti-bombe) appartient aux opt-ins forge-mvc-files / forge-mvc-images,
    # qui lisent leur config depuis l'environnement.
    "upload_max_size": 5 * 1024 * 1024,
    # Mail : aucun slot ici. Le mail est un opt-in (forge-mvc-mail, ADR-022)
    # qui lit sa configuration directement depuis l'environnement (ADR-031).
    # Le noyau ne connaît pas le mail.
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
    # I18n — langue par défaut et langue de fallback pour trans().
    "i18n_default_locale": "fr",
    "i18n_fallback_locale": "fr",
    # Store de session configurable — None = MemorySessionStore par défaut.
    # Accepte tout objet implémentant SessionStore (core.sessions.contract).
    "session_store": None,
    # Reverse proxy — IPs des proxies de confiance autorisés à fournir X-Real-IP.
    # frozenset vide par défaut : X-Real-IP est ignoré tant qu'aucun proxy
    # n'est explicitement déclaré (HTTP-TRUSTED-PROXY-IP-001).
    "trusted_proxies": frozenset(),
}

_PATH_KEYS = {"views_dir", "sql_dir"}


def configure(**kwargs: object) -> None:
    """Configure le noyau — à appeler une fois au démarrage, avant toute requête."""
    unknown = set(kwargs) - set(_cfg)
    if unknown:
        raise KeyError(f"Clés inconnues dans forge.configure() : {unknown}")
    for key, value in kwargs.items():
        if key == "session_store":
            _apply_session_store(value)
            continue
        if key in _PATH_KEYS and isinstance(value, str) and not os.path.isabs(value):
            value = os.path.join(_PROJECT_ROOT, value)
        _cfg[key] = value


def _apply_session_store(store: object) -> None:
    """Valide et injecte le store de session dans le gestionnaire."""
    from core.sessions.contract import SessionStore
    from core.sessions.manager import set_session_store
    if store is not None and not isinstance(store, SessionStore):
        raise TypeError(
            f"forge.configure(session_store=...) : valeur invalide {store!r}. "
            "Le store doit implémenter le protocole SessionStore "
            "(core.sessions.contract — méthodes : create, get, set, replace, delete, "
            "regenerate, authenticate, touch_expiry, set_flash, get_flash)."
        )
    _cfg["session_store"] = store
    set_session_store(store)


def get(key: str) -> Any:
    """Retourne une valeur de configuration du noyau.

    Type de retour `Any` (et non `object`) : le registre est **hétérogène**
    (str, int, bool, chemins, store de session…). C'est la frontière de config
    dynamique assumée ; un typage par clé (overloads / settings typé) pourra
    l'affiner ultérieurement (ADR-036, cliquet).
    """
    try:
        return _cfg[key]
    except KeyError:
        raise KeyError(f"Clé de configuration inconnue : {key!r}")
