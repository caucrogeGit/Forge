"""Tests documentaires — STARTER-WELCOME-ADMIN-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-admin`
(module opt-in `forge-mvc-admin`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
ADMIN = PROJECT_ROOT / "packages" / "forge-mvc-admin" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in ADMIN.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (ADMIN / page).read_text(encoding="utf-8")


MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-admin" / "mkdocs.yml"


def _nav_par_niveau() -> "dict[str, list[str]]":
    """Pages du parcours, par niveau, dans l'ordre du menu.

    La chaîne était figée ici, palier par palier
    (`WELCOME-ADMIN-CHAINE-DERIVEE-001`). Trois paliers ajoutés, et ce
    garde-fou tombait alors que la chaîne était intacte : il fixait la liste
    d'alors, pas la propriété.

    Le `nav` fait autorité, c'est l'ordre que le lecteur voit dans le menu.
    Chaque page doit mener à la suivante ; la dernière, au bilan.
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


class TestBilans:

    def test_debutant_mene_au_niveau_suivant(self):
        assert _has("debutant/bilan.md", "../intermediaire/admin-detail.md")

    def test_intermediaire_mene_au_niveau_suivant(self):
        assert _has("intermediaire/bilan.md", "../avance/admin-delete.md")

    def test_avance_mene_au_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")



class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
