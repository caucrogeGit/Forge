# pyright: strict
"""Namespace des vues applicatives générées (ADR-073).

Les vues de l'application (à la main ou via `make:crud`) vivent sous un dossier
dédié de `mvc/views/` (défaut `app/`), à côté de `public/` ; les dossiers du cadre
restent à la racine. Le namespace est réglé par `APP_VIEWS_NAMESPACE` dans le
`config.py` du projet ; `""` rétablit la disposition plate historique.

`make:crud` lit ce réglage au moment de la génération et le fige dans les chemins
écrits et dans les `render(...)` / `{% include %}` générés. `render()` ne lit
jamais ce réglage : les chemins sont littéraux.
"""
from __future__ import annotations

# Doit coïncider avec le défaut du squelette (config.py : APP_VIEWS_NAMESPACE).
# Un garde-fou vérifie l'égalité (VIEWS-NAMESPACE-GUARDS-001).
DEFAULT_APP_VIEWS_NAMESPACE = "app"


def resolve_app_views_namespace() -> str:
    """Lit `APP_VIEWS_NAMESPACE` du projet courant (`config.py`), tolérant.

    Retourne le namespace normalisé (sans slashes de bord) ; `""` = plat. Repli
    sur le défaut si `config.py` est absent ou illisible : la génération ne doit
    jamais échouer à cause d'une config incomplète (un projet en cours de mise en
    place peut générer un CRUD avant d'avoir un backend configuré).
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
    """Dossier de vues d'une entité, relatif à `mvc/views/` (ADR-073).

    `entity_view_dir("eleve", "app")` → `"app/eleve"` ;
    `entity_view_dir("eleve", "")`    → `"eleve"` (disposition plate).
    """
    ns = namespace.strip("/")
    return f"{ns}/{snake}" if ns else snake
