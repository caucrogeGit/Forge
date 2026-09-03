# pyright: strict
"""Route publique par slug (`ENTITIES-SLUG-ROUTES-001`).

La recherche par slug existait, `get_<snake>_by_<slug>` (ADR-017), et aucune
route ne s'en servait : une URL publique lisible demandait d'écrire la méthode
et la route à la main, dans chaque projet.

Le module vit à part de `make_crud`, qui est une **façade** et qu'un garde-fou
tient sous quatre cents lignes. Y ajouter la logique l'aurait fait déborder, et
la façade doit rester lisible d'un coup d'œil.
"""
from __future__ import annotations

from typing import Any, cast

__all__ = ["slug_field_of", "slug_route_lines", "RESERVED_SLUG_SEGMENTS"]

#: Segments fixes déclarés avant la route publique. Un slug qui vaudrait l'un
#: d'eux serait capturé par eux, et sa fiche resterait inatteignable.
#:
#: Ces valeurs sont **des données**, jamais des noms que Forge pourrait
#: refuser : c'est à l'application de les écarter à l'écriture, et cette liste
#: est là pour qu'elle sache lesquelles.
RESERVED_SLUG_SEGMENTS = (
    "new", "create", "show", "edit", "update", "destroy",
    "bulk-delete", "bulk-delete-confirm", "export-csv",
)


def slug_field_of(definition: "dict[str, Any]") -> str:
    """Nom du champ slug de l'entité, ou une chaîne vide."""
    champs = cast("list[Any]", definition.get("fields", []))
    for brut in champs:
        if not isinstance(brut, dict):
            continue
        champ = cast("dict[str, Any]", brut)
        forme = champ.get("form")
        if isinstance(forme, dict) and cast("dict[str, Any]", forme).get("field") == "slug":
            return str(champ["name"])
    return ""


def slug_route_lines(definition: "dict[str, Any]", snake: str, ctrl: str) -> "list[str]":
    """Lignes de la route publique, ou une liste vide si l'entité n'a pas de slug.

    La route est déclarée **en dernier**, après les segments fixes : un slug
    valant « new » serait sinon capturé par `/new`.
    """
    champ = slug_field_of(definition)
    if not champ:
        return []
    return [
        "",
        "    # Fiche publique adressée par son slug (ENTITIES-SLUG-ROUTES-001).",
        "    # Déclarée en dernier : un slug valant « new » ou « edit » serait",
        "    # capturé par les segments fixes ci-dessus, et resterait inatteignable.",
        f'    with router.group("/{snake}", public=True, csrf=False) as public:',
        f'        public.add("GET", "/{{{champ}}}", {ctrl}.show_by_slug,',
        f'                   name="{snake}-show_by_slug")',
    ]
