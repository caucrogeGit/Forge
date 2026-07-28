"""DOC-ROUTES-PACKAGE-REFS-001 : plus aucune référence au défunt `mvc/routes.py`.

L'ADR-068 a remplacé le fichier unique `mvc/routes.py` par un **package**
`mvc/routes/`, un fichier par contrôleur branché dans `__init__.py`.

Huit références au chemin disparu ont survécu, dont trois dans des **messages
affichés à l'utilisateur** par `forge module:routes` : elles invitaient à
éditer un fichier qui n'existe pas. Le squelette, sa suite de tests, la
documentation du routeur et l'exemple minimal du README étaient également en
retard, ce dernier enseignant en prime une forme d'API (`routes = [...]`) que
le cœur ne connaît plus.

Les archives sont exclues : `docs/history/` est la mémoire brute du projet et
les ADR décrivent l'état du jour où ils ont été écrits, y compris celui que
l'ADR-068 remplace.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

OBSOLETE_PATH = "mvc/routes.py"

#: Zones inspectées : tout ce qu'un utilisateur lit ou reçoit.
SCANNED = ("core", "cli", "skeleton", "packages", "docs", "README.md")

#: Archives et documents figés, hors périmètre.
#: `docs/roadmap/` consigne des tickets **livrés**, décrits dans les termes de
#: leur époque : réécrire leur énoncé falsifierait l'historique, au même titre
#: que `docs/history/` et les ADR.
EXCLUDED_PARTS = (
    "docs/history",
    "docs/adr",
    "docs/roadmap",
    "/build/",
    "/.venv/",
    "/__pycache__/",
    "official-site/docs/forge",
)

SUFFIXES = (".py", ".md", ".html", ".txt", ".yml")


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for entry in SCANNED:
        target = PROJECT_ROOT / entry
        if target.is_file():
            files.append(target)
            continue
        files.extend(p for p in target.rglob("*") if p.is_file() and p.suffix in SUFFIXES)
    return [
        p for p in files
        if not any(part in p.as_posix() for part in EXCLUDED_PARTS)
    ]


def test_aucune_reference_au_fichier_de_routes_disparu() -> None:
    offenders: list[str] = []
    for path in _scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover - binaire inattendu
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if OBSOLETE_PATH in line:
                offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{number}")

    assert offenders == [], (
        f"L'ADR-068 a remplacé {OBSOLETE_PATH} par le package mvc/routes/ ; "
        f"ces emplacements citent encore le chemin disparu : {offenders}"
    )


def test_le_squelette_livre_bien_le_package_de_routes() -> None:
    """Contrôle positif : le chemin de remplacement existe réellement."""
    package_init = PROJECT_ROOT / "skeleton" / "data" / "mvc" / "routes" / "__init__.py"

    assert package_init.is_file()
    assert not (PROJECT_ROOT / "skeleton" / "data" / "mvc" / "routes.py").exists()


def test_l_exemple_du_readme_suit_l_api_du_routeur() -> None:
    """Le README enseignait `routes = [...]`, forme que le cœur ne connaît plus."""
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "router = Router()" in readme
    assert "routes = [" not in readme
