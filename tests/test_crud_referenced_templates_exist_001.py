"""CRUD-REFERENCED-TEMPLATES-EXIST-001 (FORGE-11).

Garde-fou runtime que les portes statiques (pyright, ruff) ne couvrent pas :
tout composant Jinja (`components/*.html`) référencé par les vues générées par
`make:crud` doit **exister** dans les composants livrés par le squelette
(`forge new`). Sinon le rendu lève `TemplateNotFound` à l'exécution, alors que
`make check` reste vert.

Cause historique : les vues incluaient `components/button.html`, absent du
squelette (le bouton est la macro `button` de `components/ui.html`).

Charte : principe 6 (tester avant d'élargir), règle A (retirer la cause).
"""
from __future__ import annotations

import re
from pathlib import Path

from cli.entities.make_crud import (
    build_form_view,
    build_index_view,
    build_show_view,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKELETON_COMPONENTS = PROJECT_ROOT / "skeleton" / "data" / "mvc" / "views" / "components"

def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False,
           nullable=False, constraints=None, unique=False):
    col = "".join(p.capitalize() for p in name.split("_") if p)
    return {
        "name": name, "column": col, "python_type": python_type,
        "sql_type": sql_type, "nullable": nullable, "primary_key": primary_key,
        "auto_increment": auto_increment, "constraints": constraints or {}, "unique": unique,
    }


_CONTACT = {
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str", constraints={"not_empty": True}),
    ],
}

# `{% include "components/x.html" %}` ou `{% from "components/x.html" import ... %}`.
_COMPONENT_REF = re.compile(r'components/([\w-]+\.html)')


def _referenced_components(view_html: str) -> set[str]:
    return set(_COMPONENT_REF.findall(view_html))


def _generated_views() -> dict[str, str]:
    return {
        "index": build_index_view(_CONTACT),
        "show": build_show_view(_CONTACT),
        "form": build_form_view(_CONTACT),
    }


def test_composants_references_existent_dans_le_squelette():
    delivered = {p.name for p in SKELETON_COMPONENTS.glob("*.html")}
    for view_name, html in _generated_views().items():
        for component in _referenced_components(html):
            assert component in delivered, (
                f"La vue générée '{view_name}' référence components/{component}, "
                f"absent du squelette ({sorted(delivered)}). Rendu = TemplateNotFound."
            )


def test_bouton_passe_par_la_macro_ui_et_non_un_fichier_button():
    # FORGE-11 : plus aucune référence au fichier fantôme components/button.html.
    for html in _generated_views().values():
        assert "components/button.html" not in html
        assert 'from "components/ui.html" import button' in html
