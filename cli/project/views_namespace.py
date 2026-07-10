# pyright: strict
"""Namespace des vues applicatives (ADR-073).

Les vues de l'application (à la main, `make:crud` ou `make:auth`) vivent sous un
dossier dédié de `mvc/views/` (défaut `app/`), à côté de `public/` ; les dossiers
du cadre restent à la racine. Le namespace est réglé par `APP_VIEWS_NAMESPACE`
dans le `config.py` du projet ; `""` rétablit la disposition plate historique.

Ce module vit dans le **cœur** (`cli/project/`) pour être partagé par les
générateurs du cœur (`make:auth`) et de l'opt-in entités (`make:crud`), sans que
le cœur dépende de l'opt-in (ADR-070). Les générateurs lisent le réglage au moment
de la génération et le figent dans les chemins écrits et les `render(...)` /
`{% include %}` produits. `render()` ne lit jamais ce réglage : les chemins sont
littéraux.
"""
from __future__ import annotations

# Doit coïncider avec le défaut du squelette (config.py : APP_VIEWS_NAMESPACE).
# Un garde-fou vérifie l'égalité.
DEFAULT_APP_VIEWS_NAMESPACE = "app"


def resolve_app_views_namespace() -> str:
    """Lit `APP_VIEWS_NAMESPACE` du projet courant (`config.py`), tolérant.

    Retourne le namespace normalisé (sans slashes de bord) ; `""` = plat. Repli
    sur le défaut si `config.py` est absent ou illisible : la génération ne doit
    jamais échouer à cause d'une config incomplète (un projet en cours de mise en
    place peut générer avant d'avoir un backend configuré).
    """
    try:
        from cli.project.project_config import ProjectConfigError, load_project_config
    except ImportError:
        return DEFAULT_APP_VIEWS_NAMESPACE
    try:
        config = load_project_config()
    except ProjectConfigError:
        return DEFAULT_APP_VIEWS_NAMESPACE
    value = getattr(config, "APP_VIEWS_NAMESPACE", DEFAULT_APP_VIEWS_NAMESPACE)
    if not isinstance(value, str):
        return DEFAULT_APP_VIEWS_NAMESPACE
    return value.strip("/")


def entity_view_dir(snake: str, namespace: str) -> str:
    """Dossier de vues d'une brique, relatif à `mvc/views/` (ADR-073).

    `entity_view_dir("eleve", "app")` → `"app/eleve"` ;
    `entity_view_dir("auth", "")`     → `"auth"` (disposition plate).
    """
    ns = namespace.strip("/")
    return f"{ns}/{snake}" if ns else snake
