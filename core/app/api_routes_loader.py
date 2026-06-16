# pyright: strict
"""Chargement optionnel de mvc/api_routes.py."""
import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_api_routes(router: Any, module_path: str = "mvc.api_routes") -> None:
    """Charge module_path si présent et appelle register_api_routes(router).

    Absent → retour silencieux (normal).
    Présent et valide → register_api_routes(router) appelé.
    Présent mais invalide (erreur Python) → ImportError levé.
    Présent sans register_api_routes → avertissement, aucune route ajoutée.
    """
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        # Absent → silencieux UNIQUEMENT si c'est `module_path` lui-même (ou un
        # de ses paquets parents) qui manque. Si `module_path` existe mais
        # importe un module supprimé (ex. `media`, `core.uploads`), l'erreur
        # porte le nom de cet autre module → on la remonte au lieu de la masquer.
        if exc.name and (exc.name == module_path or module_path.startswith(exc.name + ".")):
            return
        raise ImportError(f"Erreur dans {module_path} : {exc}") from exc
    except Exception as exc:
        raise ImportError(f"Erreur dans {module_path} : {exc}") from exc
    if hasattr(mod, "register_api_routes"):
        getattr(mod, "register_api_routes")(router)
    else:
        logger.warning("Module %s présent mais sans register_api_routes()", module_path)
