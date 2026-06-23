"""Tests — LANDING-INSTALL-CARDS-001.

Verrouille le contrat de la section « Installer Forge selon votre usage »
de la landing canonique (`docs/index.html`).

Depuis la refonte des cartes, la section ne contient plus que **2 cartes**,
au même design, qui orientent par contexte de poste :

  1. Poste Linux                 → docs/install/poste-linux.md   (data-install-card="pipx-user")
  2. Poste Windows 10/11 + WSL   → docs/install/windows-wsl.md   (data-install-card="windows-wsl")

Décisions assumées :
- Les anciennes cartes « Développement du core » et « Production WSGI » ont
  été retirées de la section Installation : la landing oriente par poste, et
  la carte Windows renvoie elle-même vers la procédure du poste Linux.
- Les cartes sont volontairement légères (orientation, pas de procédure
  détaillée) : le détail vit dans les pages d'installation.

`docs/index.html` est généré par `forge sync:landing` — on contrôle la
synchronisation côté tests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

LANDING = Path("docs/index.html")
DOCS_LANDING = Path("docs/index.html")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")

# Pages cibles attendues — toutes doivent exister sous docs/.
EXPECTED_TARGETS = [
    Path("docs/install/poste-linux.md"),
    Path("docs/install/windows-wsl.md"),
]


def _src() -> str:
    return LANDING.read_text(encoding="utf-8")


def _docs() -> str:
    return DOCS_LANDING.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Synchronisation source canonique ↔ docs/index.html
# ---------------------------------------------------------------------------


class TestSync:
    def test_landing_source_existe(self):
        assert LANDING.exists()

    def test_docs_index_existe(self):
        assert DOCS_LANDING.exists()

    def test_docs_index_pointe_vers_install(self):
        """docs/index.html, généré par `forge sync:landing`, doit refléter
        les chemins install/ des 2 cartes."""
        docs = _docs()
        assert "install/poste-linux/" in docs
        assert "install/windows-wsl/" in docs


# ---------------------------------------------------------------------------
# Section Installation — présente, structurée, intitulée correctement
# ---------------------------------------------------------------------------


class TestInstallationSection:
    def test_section_id_present(self):
        assert 'id="installation"' in _src()

    def test_titre_section(self):
        assert "Installer Forge." in _src()

    def test_grille_2_cards(self):
        text = _src()
        # 2 cards, identifiables par data-install-card="...", dans l'ordre source.
        cards = re.findall(r'data-install-card="([^"]+)"', text)
        assert cards == [
            "pipx-user",
            "windows-wsl",
        ], f"Cards installation incorrectes ou désordonnées : {cards}"

    def test_aucune_card_install_en_col_span_2(self):
        """Les 2 cards doivent suivre le même design — aucune ne doit
        utiliser md:col-span-2."""
        text = _src()
        for marker in (
            'data-install-card="pipx-user"',
            'data-install-card="windows-wsl"',
        ):
            idx = text.find(marker)
            div_start = text.rfind("<", 0, idx)
            div_end = text.find(">", idx)
            tag = text[div_start:div_end]
            assert "md:col-span-2" not in tag, (
                f"La card {marker} utilise md:col-span-2 — toutes les cards "
                "d'installation doivent avoir le même design."
            )


# ---------------------------------------------------------------------------
# Card 1 — Poste Linux (pipx)
# ---------------------------------------------------------------------------


def _pipx_card() -> str:
    text = _src()
    idx = text.find('data-install-card="pipx-user"')
    end = text.find('data-install-card="windows-wsl"')
    return text[idx:end]


class TestCardPosteLinux:
    def test_card_presente(self):
        assert 'data-install-card="pipx-user"' in _src()

    def test_titre(self):
        assert "Poste Linux" in _pipx_card()

    def test_distributions_supportees(self):
        block = _pipx_card()
        assert "Debian" in block
        assert "Ubuntu" in block
        assert "Linux Mint" in block

    def test_valorise_pipx_et_forge_new(self):
        block = _pipx_card()
        assert "pipx" in block
        assert "forge new" in block

    def test_lien_cible(self):
        assert "/docs/forge/install/poste-linux/" in _pipx_card()


# ---------------------------------------------------------------------------
# Card 2 — Poste Windows 10/11 + WSL
# ---------------------------------------------------------------------------


def _wsl_card() -> str:
    text = _src()
    idx = text.find('data-install-card="windows-wsl"')
    end = text.find("</section>", idx)
    return text[idx:end]


class TestCardWindowsWsl:
    def test_card_presente(self):
        assert 'data-install-card="windows-wsl"' in _src()

    def test_titre(self):
        assert "Poste Windows 10/11 + WSL" in _src()

    def test_valorise_wsl_ubuntu_24_04(self):
        block = _wsl_card()
        assert "WSL" in block
        assert "Ubuntu 24.04" in block

    def test_renvoie_vers_procedure_poste_linux(self):
        # La carte Windows oriente vers la procédure du poste Linux.
        block = _wsl_card()
        assert "poste Linux" in block

    def test_lien_cible(self):
        assert "/docs/forge/install/windows-wsl/" in _src()


# ---------------------------------------------------------------------------
# Liens — pas de page cible cassée
# ---------------------------------------------------------------------------


class TestNoBrokenTargets:
    @pytest.mark.parametrize("target", EXPECTED_TARGETS, ids=lambda p: str(p))
    def test_target_page_exists(self, target: Path):
        assert target.exists(), (
            f"Cible attendue absente : {target} — la landing pointerait "
            "vers un lien cassé."
        )


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "LANDING-INSTALL-CARDS-001" in text

    def test_ticket_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "LANDING-INSTALL-CARDS-001" in line:
                assert "livré" in line.lower(), (
                    f"LANDING-INSTALL-CARDS-001 non marqué comme livré : {line}"
                )
                return
        pytest.fail("Ligne LANDING-INSTALL-CARDS-001 introuvable.")


# ---------------------------------------------------------------------------
# Build MkDocs strict — garde-fou final
# ---------------------------------------------------------------------------


class TestMkdocsBuild:
    def test_mkdocs_build_strict(self):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mkdocs build --strict a échoué :\n{result.stderr}"
        )
