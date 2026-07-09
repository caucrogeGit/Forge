"""Garde-fou LANDING-CARDS-LINKS-ORDER-001.

Contrat public de la landing page :
- ordre des sections (Installation avant les cartes) ;
- 21 cartes présentes par titre ;
- liens absolus uniquement ;
- modules opt-in conservés ;
- aucune trace interne Forge 3.x dans la landing publique.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING = PROJECT_ROOT / "docs" / "index.html"

EXPECTED_CARD_TITLES = [
    "HTTP &amp; routing",
    "MVC",
    "Templates Jinja",
    "SQL visible",
    "Entités JSON",
    "Migrations",
    "CRUD généré",
    "Formulaires",
    "Sécurité",
    "Auth/User",
    "Front léger",
    "JSON Schema",
    "CLI Forge",
    "Déploiement",
    "API JSON légère",
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
]

FORGE_3X_FORBIDDEN = [
    "Forge 3",
    "Forge 3.0",
    "3.0.0",
    "3.0.2",
    "3.0.6",
    "série 3.x",
    "Après 3.0",
]


class TestSectionOrder:
    """Installation apparaît avant la section des cartes."""

    def test_installation_before_cards(self):
        text = LANDING.read_text(encoding="utf-8")
        pos_install = text.find('id="installation"')
        pos_cards   = text.find("Modules officiels installables séparément")
        assert pos_install != -1, "Section installation introuvable (id='installation')"
        assert pos_cards   != -1, "Section des modules officiels introuvable"
        assert pos_install < pos_cards, (
            "La section Installation doit apparaître avant la section des cartes. "
            f"(positions : installation={pos_install}, cartes={pos_cards})"
        )


class TestCardTitles:
    """Les 21 cartes sont présentes par titre."""

    @pytest.mark.parametrize("title", EXPECTED_CARD_TITLES)
    def test_card_title_present(self, title: str):
        text = LANDING.read_text(encoding="utf-8")
        assert title in text, (
            f"Carte '{title}' manquante dans la landing."
        )


class TestCardLinks:
    """Les liens des cartes sont racine-relatifs (/docs/forge/…) et non génériques."""

    def test_all_card_links_root_relative(self):
        text = LANDING.read_text(encoding="utf-8")
        hrefs = re.findall(r'<a\s+href="([^"]+)"\s+class="block group"', text)
        invalid = [h for h in hrefs if not (h.startswith("/docs/forge/") or h.startswith("http"))]
        assert not invalid, (
            f"Liens de carte non conformes (attendu /docs/forge/… ou http) : {invalid}"
        )

    def test_no_overly_generic_links(self):
        """Les cartes Sécurité, Auth, Mail ne doivent pas pointer vers concepts/."""
        text = LANDING.read_text(encoding="utf-8")
        blocks = re.findall(
            r'<a\s+href="([^"]+)"\s+class="block group"[^>]*>.*?</a>',
            text, re.DOTALL,
        )
        for block in blocks:
            href_match = re.search(r'href="([^"]+)"', block)
            title_match = re.search(r'group-hover:landing-accent-text[^>]*>([^<]+)<', block)
            if not href_match or not title_match:
                continue
            href = href_match.group(1)
            title = title_match.group(1).strip()
            if title in ("Sécurité", "Auth/User"):
                assert "concepts" not in href, (
                    f"La carte '{title}' pointe vers une page trop générique : {href}"
                )


class TestOptInModules:
    """Les modules opt-in listés sur la landing sont présents avec leurs cartes."""

    @pytest.mark.parametrize("module", [
        "forge-mvc-mfa",
        "forge-mvc-rbac",
        "forge-mvc-workflow",
        "forge-mvc-stats",
        "forge-mvc-files",
        "forge-mvc-images",
        "forge-mvc-iot",
        "forge-mvc-video",
        "forge-mvc-audio",
        "forge-mvc-mail",
        "forge-mvc-entities",
        "forge-mvc-i18n",
    ])
    def test_module_card_present(self, module: str):
        text = LANDING.read_text(encoding="utf-8")
        assert module in text, f"Module opt-in '{module}' manquant dans la landing."

    def test_modules_description_wording(self):
        """Le bloc des modules opt-in porte son chapeau canonique
        « Modules officiels installables séparément. »."""
        text = LANDING.read_text(encoding="utf-8")
        assert "Modules officiels installables séparément" in text, (
            "Le bloc des modules opt-in doit porter son chapeau canonique."
        )
        assert "installables séparément" in text, (
            "Le bloc des modules opt-in doit indiquer qu'ils s'installent séparément."
        )


class TestNoForge3xTraces:
    """La landing publique ne contient aucune trace interne Forge 3.x."""

    @pytest.mark.parametrize("forbidden", FORGE_3X_FORBIDDEN)
    def test_no_forge3x_string(self, forbidden: str):
        text = LANDING.read_text(encoding="utf-8")
        assert forbidden not in text, (
            f"Trace interne '{forbidden}' présente dans la landing publique "
            f"(LANDING-CARDS-LINKS-ORDER-001)."
        )


# ---------------------------------------------------------------------------
# Parcours welcome : chaque paquet qui en a un est lié depuis la landing
# ---------------------------------------------------------------------------

PACKAGES_DIR = PROJECT_ROOT / "packages"


def _packages_with_welcome() -> list[str]:
    """Slugs (nom sans le préfixe forge-mvc-) des paquets dotés d'un parcours
    welcome, hors infrastructure de test (dev-only, absente de la landing)."""
    slugs = []
    for pkg in sorted(PACKAGES_DIR.iterdir()):
        if pkg.name == "forge-mvc-testing":
            continue
        if (pkg / "docs" / "welcome").is_dir():
            slugs.append(pkg.name.removeprefix("forge-mvc-"))
    return slugs


@pytest.mark.parametrize("slug", _packages_with_welcome())
def test_parcours_welcome_lie_depuis_la_landing(slug: str):
    """Tout paquet doté d'un parcours welcome (opt-in fonctionnel ou backend
    BDD) doit être présenté dans la section Starters de la landing. Dérivé de
    packages/, donc drift-proof : un nouveau parcours non lié fait échouer ce
    test (c'est ce qui manquait pour les backends BDD)."""
    text = LANDING.read_text(encoding="utf-8")
    assert f"/docs/forge/{slug}/welcome/" in text, (
        f"Le parcours welcome de forge-mvc-{slug} n'est pas lié depuis la "
        f"landing (section Starters). Attendu : /docs/forge/{slug}/welcome/..."
    )
