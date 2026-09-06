"""Tests documentaires — STARTER-WELCOME-RBAC-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-rbac`
(module opt-in `forge-mvc-rbac`, 3 niveaux) : chaînage des paliers, bilans, et
absence de commande de création dans les pages (`installation.md` exempté).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
RBAC = PROJECT_ROOT / "packages" / "forge-mvc-rbac" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in RBAC.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (RBAC / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/rbac-welcome.md", "(rbac-permission.md)")
        assert _has("debutant/rbac-permission.md", "(rbac-role.md)")
        assert _has("debutant/rbac-role.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/rbac-check.md")


MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-rbac" / "mkdocs.yml"


def _nav_par_niveau() -> "dict[str, list[str]]":
    """Pages du parcours, par niveau, dans l'ordre du menu.

    La chaîne était figée page par page (`WELCOME-RBAC-CHAINE-DERIVEE-001`).
    Quatre paliers ajoutés, et ce garde-fou tombait alors que la chaîne était
    intacte : il fixait la liste d'alors, pas la propriété.
    """
    niveaux: "dict[str, list[str]]" = {}
    for ligne in MKDOCS.read_text(encoding="utf-8").splitlines():
        trouve = re.search(r"(welcome/(debutant|intermediaire|avance)/([\w-]+\.md))\s*$", ligne)
        if trouve:
            niveaux.setdefault(trouve.group(2), []).append(trouve.group(3))
    return niveaux


@pytest.mark.parametrize("niveau", ["debutant", "intermediaire", "avance"])
def test_chaque_palier_mene_au_suivant(niveau: str) -> None:
    """Aucun cul-de-sac : le lecteur doit toujours savoir où aller."""
    pages_du_niveau = _nav_par_niveau()[niveau]

    assert pages_du_niveau[-1] == "bilan.md", f"{niveau} ne finit pas par son bilan"
    for courante, suivante in zip(pages_du_niveau, pages_du_niveau[1:]):
        assert _has(f"{niveau}/{courante}", f"({suivante})"), (
            f"{niveau}/{courante} ne mène pas à {suivante}")


class TestBilansEnchaines:

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/rbac-user-role.md")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")

class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
