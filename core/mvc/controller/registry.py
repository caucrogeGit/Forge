"""Registre de fournisseurs de contexte Jinja — pattern push (charte principe 8).

Les modules opt-in (forge-mvc-rbac, etc.) s'enregistrent eux-mêmes via
register_jinja_context_provider(). BaseController itère sur les fournisseurs
sans nommer nominalement aucun module opt-in.
"""
from __future__ import annotations

from typing import Any, Callable

_providers: list[Callable[[Any], dict[str, Any]]] = []


def register_jinja_context_provider(fn: Callable[[Any], dict[str, Any]]) -> None:
    """Enregistre un fournisseur de contexte Jinja2."""
    _providers.append(fn)


def iter_jinja_context_providers() -> list[Callable[[Any], dict[str, Any]]]:
    """Retourne une copie de la liste des fournisseurs enregistrés."""
    return list(_providers)


def _clear_for_tests() -> None:
    """Vide le registre — usage tests uniquement."""
    _providers.clear()
