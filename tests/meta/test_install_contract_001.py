"""Garde-fou DEV-INSTALL-CONTRACT-FIX-001.

Vérifie que les guides d'installation officiels respectent l'ordre canonique :
  python -m pip install -e .
  python -m pip install -r requirements-dev.txt

Si l'ordre est inversé, pip peut résoudre forge-mvc==<version> depuis PyPI
(déclaré comme dépendance des opt-in) au lieu du checkout local : en mode dev
on veut le core depuis les sources (`-e .`), et la version publiée étant une
bêta (`1.0.0-beta.x`) elle exigerait `--pre`. D'où l'ordre canonique.

Périmètre : guides qui s'adressent au contributeur/développeur (mode dev),
pas les guides utilisateur final (qui ne devraient pas avoir besoin de
requirements-dev.txt).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

DEV_GUIDES = [
    PROJECT_ROOT / "docs" / "install" / "core-dev.md",
    PROJECT_ROOT / "docs" / "install" / "github.md",
    PROJECT_ROOT / "CONTRIBUTING.md",
    PROJECT_ROOT / "README.md",
]


def test_dev_guides_install_core_before_requirements_dev():
    """Dans chaque guide dev, 'pip install -e .' doit précéder
    'pip install -r requirements-dev.txt' si les deux commandes
    coexistent dans le même bloc bash."""
    offenders: list[str] = []
    for guide in DEV_GUIDES:
        if not guide.exists():
            continue
        text = guide.read_text(encoding="utf-8")
        for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
            has_editable = re.search(r"pip install\s+-e\s+\.", block)
            has_dev_req = re.search(
                r"pip install\s+-r\s+requirements-dev\.txt", block
            )
            if not (has_editable and has_dev_req):
                continue
            if has_editable.start() > has_dev_req.start():
                offenders.append(
                    f"{guide.relative_to(PROJECT_ROOT)} : ordre inversé "
                    f"(pip install -e . devrait précéder requirements-dev.txt)"
                )

    if offenders:
        raise AssertionError(
            f"{len(offenders)} guide(s) avec ordre d'install inversé :\n"
            + "\n".join(f"  - {o}" for o in offenders)
        )


def test_no_pypi_install_in_dev_guides():
    """Aucun guide dev ne doit proposer 'pip install forge-mvc[...]' (PyPI)
    sans avertissement explicite : en mode dev on installe le core depuis
    les sources (`-e .`), pas depuis la bêta PyPI (qui exigerait `--pre`)."""
    offenders: list[str] = []
    for guide in DEV_GUIDES:
        if not guide.exists():
            continue
        text = guide.read_text(encoding="utf-8")
        problematic = re.findall(
            r'`?pip install ["\']?forge-mvc[\[\w,\]"\']*`?',
            text,
        )
        problematic = [
            p for p in problematic
            if "pip install -e" not in p and "pip install -r" not in p
        ]
        if problematic:
            has_warning = any(
                marker in text.lower()
                for marker in (
                    "mode source-only",
                    "n'est pas publié",
                    "publication pypi",
                    "publication prévue",
                )
            )
            if not has_warning:
                offenders.append(
                    f"{guide.relative_to(PROJECT_ROOT)} : commande "
                    f"PyPI sans avertissement : {problematic[0]}"
                )

    if offenders:
        raise AssertionError(
            f"{len(offenders)} guide(s) sans avertissement source-only :\n"
            + "\n".join(f"  - {o}" for o in offenders)
        )
