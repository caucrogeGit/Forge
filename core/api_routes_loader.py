"""Chargement optionnel de mvc/api_routes.py."""
import importlib
import logging

logger = logging.getLogger(__name__)


def load_api_routes(router, module_path="mvc.api_routes"):
    """Charge module_path si présent et appelle register_api_routes(router).

    Absent → retour silencieux (normal).
    Présent et valide → register_api_routes(router) appelé.
    Présent mais invalide (erreur Python) → ImportError levé.
    Présent sans register_api_routes → avertissement, aucune route ajoutée.
    """
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return
    except Exception as exc:
        raise ImportError(f"Erreur dans {module_path} : {exc}") from exc
    if hasattr(mod, "register_api_routes"):
        mod.register_api_routes(router)
    else:
        logger.warning("Module %s présent mais sans register_api_routes()", module_path)
