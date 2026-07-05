# pyright: strict
"""Format canonique du registre d'opt-ins d'un projet (`optins/registry.py`).

ADR-061 : le projet porte un registre unique et visible de ses opt-ins, à la
manière du `config/bundles.php` de Symfony. Le code des opt-ins reste dans le
`.venv` ; ce fichier n'est qu'une vue déclarative et explicite (aucune
découverte automatique).

Ce module est la **source unique** du gabarit :

- `REGISTRY_TEMPLATE` est le contenu posé par `forge new` (squelette) et, à
  défaut, recréé par `forge opt-in:enable`. Un garde-fou vérifie que la copie du
  squelette lui est identique.
- Les ancres (`ANCHOR_*`) marquent les zones gérées par `enable`/`disable` et
  `db:*` (inscription d'un opt-in, câblage de route, backend BDD).
- Les lecteurs (`read_backend`, `read_enabled_optins`) analysent le **texte** du
  registre sans l'importer (comme `opt-in:list`, qui ne charge aucun module de
  projet).
"""
from __future__ import annotations

import ast
import re
from typing import cast

# Ancres d'insertion (gérées par forge opt-in:enable / disable, forge db:*).
ANCHOR_REGISTRY = "    # >>> opt-in registry (géré par forge opt-in:enable / disable)"
ANCHOR_IMPORT = "# >>> opt-in imports (gérés par forge opt-in:enable / disable)"
ANCHOR_CALL = "    # >>> opt-in calls (gérés par forge opt-in:enable / disable)"

REGISTRY_TEMPLATE = f'''\
# pyright: strict
"""Registre des opt-ins de ce projet (ADR-061).

Vue unique et explicite des opt-ins utilisés par ce projet. Aucun code d'opt-in
n'est copié ici : il vit dans le `.venv`. Ce fichier est géré par
`forge opt-in:enable` / `disable` et `forge db:*` ; il reste éditable à la main.

- `BACKEND` : le backend base de données choisi (ADR-054/060), ou None.
- `ENABLED_OPTINS` : les opt-ins utilisés, par nom vers catégorie d'intégration
  (route, library, crosscutting, cli). Les opt-ins `route` sont aussi câblés
  dans `register_optins` ; les autres y figurent pour la visibilité.
- `register_optins` : câble les routes des opt-ins `route` activés. Appelé
  depuis `mvc/routes.py` :

    from optins.registry import register_optins

    register_optins(router)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.http.router import Router

# Backend base de données (ADR-054/060). None tant qu'aucun n'est configuré.
BACKEND: str | None = None

# Opt-ins utilisés par ce projet : nom vers catégorie d'intégration.
ENABLED_OPTINS: dict[str, str] = {{
{ANCHOR_REGISTRY}
}}

{ANCHOR_IMPORT}


def register_optins(router: Router) -> None:
    """Branche les routes des opt-ins « route » activés dans ce projet."""
{ANCHOR_CALL}
    return None
'''


def _module(text: str) -> ast.Module:
    return ast.parse(text)


def read_backend(text: str) -> str | None:
    """Valeur littérale de `BACKEND` dans le texte d'un registre (ou None)."""
    for node in _module(text).body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "BACKEND" in targets:
                value = ast.literal_eval(node.value)
                return value if isinstance(value, str) else None
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "BACKEND" and node.value is not None:
                value = ast.literal_eval(node.value)
                return value if isinstance(value, str) else None
    return None


def read_enabled_optins(text: str) -> dict[str, str]:
    """Dictionnaire `ENABLED_OPTINS` (nom vers catégorie) lu dans le texte."""
    for node in _module(text).body:
        target_names: list[str] = []
        value_node: ast.expr | None = None
        if isinstance(node, ast.Assign):
            target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_names = [node.target.id]
            value_node = node.value
        if "ENABLED_OPTINS" in target_names and value_node is not None:
            value = ast.literal_eval(value_node)
            if isinstance(value, dict):
                items = cast("dict[object, object]", value)
                return {str(k): str(v) for k, v in items.items()}
    return {}


# ── Écriture d'une entrée ENABLED_OPTINS (gérée par enable / disable) ─────────

def registry_entry_line(name: str, kind: str) -> str:
    """Ligne déclarative d'un opt-in dans ENABLED_OPTINS (indentée dans le dict)."""
    return f'    "{name}": "{kind}",'


def add_optin_entry(text: str, name: str, kind: str) -> tuple[str, str]:
    """Insère l'entrée `name: kind` sous ANCHOR_REGISTRY (idempotent).

    Retourne `(nouveau_texte, statut)`, `statut` ∈ {"inserted", "already",
    "unrecognized"}. N'insère que la ligne d'entrée, jamais d'autre code.
    """
    if name in read_enabled_optins(text):
        return text, "already"
    if ANCHOR_REGISTRY not in text:
        return text, "unrecognized"
    line = registry_entry_line(name, kind)
    new = text.replace(ANCHOR_REGISTRY, ANCHOR_REGISTRY + "\n" + line, 1)
    return new, "inserted"


def remove_optin_entry(text: str, name: str) -> str:
    """Retire l'entrée de `name` de ENABLED_OPTINS (idempotent)."""
    pattern = re.compile(rf'^\s*"{re.escape(name)}"\s*:\s*".*",?\s*$')
    kept = [ln for ln in text.splitlines(keepends=True) if not pattern.match(ln)]
    return "".join(kept)


_BACKEND_ASSIGN = re.compile(r"^(BACKEND\s*(?::[^=]+)?=\s*).*$", re.MULTILINE)


def set_backend(text: str, name: str | None) -> str:
    """Fixe la valeur de `BACKEND` dans le texte du registre (idempotent).

    `name=None` remet à None. Ne touche que la ligne d'affectation de BACKEND ;
    laisse le texte inchangé si aucune affectation n'est trouvée.
    """
    literal = "None" if name is None else f'"{name}"'
    new, count = _BACKEND_ASSIGN.subn(lambda m: m.group(1) + literal, text, count=1)
    return new if count else text
