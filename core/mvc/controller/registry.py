# pyright: strict
"""Registres push pour Jinja — contexte et loaders de templates (charte principe 8).

Les modules opt-in (forge-mvc-rbac, forge-mvc-admin, etc.) s'enregistrent
eux-mêmes : un fournisseur de contexte via register_jinja_context_provider(), un
loader de templates via register_jinja_template_loader() (ADR-046). Le cœur itère
sur ces registres sans nommer nominalement aucun module opt-in.
"""
from __future__ import annotations

from typing import Any, Callable

__all__ = [
    "register_jinja_context_provider",
    "iter_jinja_context_providers",
    "register_jinja_template_loader",
    "iter_jinja_template_loaders",
    "_clear_for_tests",
]

_providers: list[Callable[[Any], dict[str, Any]]] = []

# Loaders de templates Jinja contribués par les opt-ins (ADR-046). Le type reste
# `Any` pour ne pas faire dépendre ce module du paquet jinja2 : le renderer
# (integrations/jinja2) sait que ce sont des `jinja2.BaseLoader`.
_template_loaders: list[Any] = []


def register_jinja_context_provider(fn: Callable[[Any], dict[str, Any]]) -> None:
    """Enregistre un fournisseur de contexte Jinja2."""
    _providers.append(fn)


def iter_jinja_context_providers() -> list[Callable[[Any], dict[str, Any]]]:
    """Retourne une copie de la liste des fournisseurs enregistrés."""
    return list(_providers)


def register_jinja_template_loader(loader: Any) -> None:
    """Enregistre un loader de templates Jinja contribué par un opt-in (ADR-046).

    L'opt-in s'enregistre lui-même à l'import (ex. `PackageLoader`). Le renderer
    compose ces loaders APRÈS le dossier `mvc/views/` du projet : un template du
    projet de même chemin masque donc le template par défaut du paquet.
    """
    _template_loaders.append(loader)


def iter_jinja_template_loaders() -> list[Any]:
    """Retourne une copie de la liste des loaders d'opt-in enregistrés."""
    return list(_template_loaders)


def _clear_for_tests() -> None:
    """Vide les registres (contexte + loaders) — usage tests uniquement."""
    _providers.clear()
    _template_loaders.clear()
