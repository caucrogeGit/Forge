# pyright: strict
"""Namespace des vues applicatives — ré-export du cœur (ADR-073).

La définition canonique vit dans le cœur (`cli.project.views_namespace`) pour être
partagée par `make:auth` (cœur) et `make:crud` (cet opt-in), sans que le cœur
dépende de l'opt-in. Ce module ré-exporte l'API pour les imports internes du CRUD.
"""
from __future__ import annotations

from cli.project.views_namespace import (
    DEFAULT_APP_VIEWS_NAMESPACE,
    entity_view_dir,
    resolve_app_views_namespace,
)

__all__ = [
    "DEFAULT_APP_VIEWS_NAMESPACE",
    "entity_view_dir",
    "resolve_app_views_namespace",
]
