"""Tests — LANDING-INSTALL-CARDS-001 (réaligné par LANDING-PUBLIC-CONTRACT-REALIGN-001).

Verrouille le contrat de la section « Installer Forge selon votre usage »
de la landing canonique (`mvc/views/landing/index.html`) après réalignement
en 4 cards toutes au même design (pas de col-span-2, pas de card spéciale) :

  1. Windows + WSL          → docs/install/windows-wsl.md
  2. Utilisateur — pipx     → docs/install/pipx.md
  3. Développement du core  → docs/install/core-dev.md
  4. Production WSGI        → docs/install/production.md
                              (entrée vers wsgi-deployment / production-limits / deployment)

Décision de suppression assumée :
- La 5e card historique « Bonjour Forge » a été retirée de la section
  Installation. Le starter `welcome` reste affiché plus bas dans
  « Starters progressifs » (carte « Bienvenue dans Forge »).

`docs/index.html` est généré par `forge sync:landing` — on contrôle la
synchronisation côté tests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

LANDING = Path("mvc/views/landing/index.html")
DOCS_LANDING = Path("docs/index.html")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")

# Pages cibles attendues — toutes doivent exister sous docs/.
EXPECTED_TARGETS = [
    Path("docs/install/windows-wsl.md"),
    Path("docs/install/pipx.md"),
    Path("docs/install/core-dev.md"),
    Path("docs/install/production.md"),
    Path("docs/wsgi-deployment.md"),
    Path("docs/production-limits.md"),
    Path("docs/deployment.md"),
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

    def test_docs_index_pointe_vers_nouvelle_install(self):
        """docs/index.html, généré par `forge sync:landing`, doit refléter
        les nouveaux chemins install/."""
        docs = _docs()
        assert "install/pipx/" in docs
        assert "install/core-dev/" in docs
        assert "install/windows-wsl/" in docs


# ---------------------------------------------------------------------------
# Section Installation — présente, structurée, intitulée correctement
# ---------------------------------------------------------------------------


class TestInstallationSection:
    def test_section_id_present(self):
        assert 'id="installation"' in _src()

    def test_titre_section(self):
        assert "Installer Forge selon votre usage" in _src()

    def test_grille_4_cards(self):
        text = _src()
        # 4 cards, identifiables par data-install-card="..."
        cards = re.findall(r'data-install-card="([^"]+)"', text)
        assert cards == [
            "windows-wsl",
            "pipx-user",
            "core-dev",
            "production",
        ], f"Cards installation incorrectes ou désordonnées : {cards}"

    def test_aucune_card_install_en_col_span_2(self):
        """Toutes les cards doivent suivre le même design — aucune ne doit
        utiliser md:col-span-2 (la card Production n'est pas spéciale)."""
        text = _src()
        for marker in (
            'data-install-card="windows-wsl"',
            'data-install-card="pipx-user"',
            'data-install-card="core-dev"',
            'data-install-card="production"',
        ):
            idx = text.find(marker)
            # On extrait les classes du <div> qui contient ce marker.
            div_start = text.rfind("<div ", 0, idx)
            div_end = text.find(">", idx)
            div_tag = text[div_start:div_end]
            assert "md:col-span-2" not in div_tag, (
                f"La card {marker} utilise md:col-span-2 — toutes les cards "
                "d'installation doivent avoir le même design."
            )


# ---------------------------------------------------------------------------
# Card 1 — Windows + WSL
# ---------------------------------------------------------------------------


class TestCardWindowsWsl:
    def test_card_presente(self):
        assert 'data-install-card="windows-wsl"' in _src()

    def test_titre(self):
        assert "Windows + WSL" in _src()

    def test_valorise_wsl_ubuntu_24_04(self):
        text = _src()
        assert "Ubuntu-24.04" in text or "Ubuntu 24.04" in text

    def test_valorise_pipx(self):
        text = _src()
        idx = text.find('data-install-card="windows-wsl"')
        end = text.find('data-install-card="pipx-user"')
        card_block = text[idx:end]
        assert "pipx" in card_block

    def test_valorise_forge_admin(self):
        text = _src()
        idx = text.find('data-install-card="windows-wsl"')
        end = text.find('data-install-card="pipx-user"')
        card_block = text[idx:end]
        assert "forge_admin" in card_block

    def test_valorise_node_20(self):
        text = _src()
        idx = text.find('data-install-card="windows-wsl"')
        end = text.find('data-install-card="pipx-user"')
        card_block = text[idx:end]
        assert "nodejs" in card_block or "Node.js 20" in card_block

    def test_avertit_contre_mnt_c(self):
        text = _src()
        idx = text.find('data-install-card="windows-wsl"')
        end = text.find('data-install-card="pipx-user"')
        card_block = text[idx:end]
        assert "/mnt/c" in card_block
        assert "~/Projets" in card_block

    def test_lien_cible(self):
        text = _src()
        assert "forgemvc.com/docs/forge/install/windows-wsl/" in text


# ---------------------------------------------------------------------------
# Card 2 — Utilisateur du framework (pipx)
# ---------------------------------------------------------------------------


class TestCardPipxUser:
    def test_card_presente(self):
        assert 'data-install-card="pipx-user"' in _src()

    def test_titre_mentionne_pipx(self):
        text = _src()
        assert "Utilisateur du framework" in text and "pipx" in text

    def test_commande_pipx_canonique(self):
        text = _src()
        # La commande recommandée doit apparaître textuellement.
        assert 'pipx install --pip-args="--pre" forge-mvc' in text

    def test_paquet_correct_forge_mvc(self):
        text = _src()
        idx = text.find('data-install-card="pipx-user"')
        end = text.find('data-install-card="core-dev"')
        card_block = text[idx:end]
        assert "forge-mvc" in card_block

    def test_avertit_de_ne_pas_installer_paquet_forge(self):
        text = _src()
        idx = text.find('data-install-card="pipx-user"')
        end = text.find('data-install-card="core-dev"')
        card_block = text[idx:end]
        normalized = " ".join(card_block.split())
        # Avertissement explicite contre le mauvais paquet.
        assert (
            "Ne pas installer le paquet" in normalized
            or "ne pas installer le paquet" in normalized.lower()
        )

    def test_lien_cible(self):
        text = _src()
        assert "forgemvc.com/docs/forge/install/pipx/" in text


# ---------------------------------------------------------------------------
# Card 3 — Développement du core (après INSTALL-CORE-DEV-DOCS-AUDIT-001)
# ---------------------------------------------------------------------------


class TestCardCoreDev:
    def test_card_presente(self):
        assert 'data-install-card="core-dev"' in _src()

    def test_titre(self):
        text = _src()
        assert "Développement du core" in text

    def test_5_validations_canoniques_listees(self):
        """La card doit montrer les 5 validations canoniques avant commit
        (pytest, compileall, ruff, mkdocs --strict, git diff --check)."""
        text = _src()
        idx = text.find('data-install-card="core-dev"')
        end = text.find('data-install-card="production"')
        card_block = text[idx:end]
        for cmd in [
            "python -m pytest",
            "python -m compileall -q .",
            "ruff check .",
            "mkdocs build --strict",
            "git diff --check",
        ]:
            assert cmd in card_block, f"Commande manquante : {cmd}"

    def test_installation_editable_pas_pipx(self):
        """La note doit préciser que l'installation est éditable, pas
        via pipx."""
        text = _src()
        idx = text.find('data-install-card="core-dev"')
        end = text.find('data-install-card="production"')
        card_block = text[idx:end]
        normalized = " ".join(card_block.split())
        assert "éditable" in normalized
        assert "pipx" in normalized

    def test_lien_principal_avec_accent(self):
        """Le CTA est en accent (comme les autres cards)."""
        text = _src()
        idx = text.find('data-install-card="core-dev"')
        end = text.find('data-install-card="production"')
        card_block = text[idx:end]
        assert "landing-accent-bg" in card_block
        assert "forgemvc.com/docs/forge/install/core-dev/" in card_block


# ---------------------------------------------------------------------------
# Card 4 — Production WSGI
# ---------------------------------------------------------------------------


class TestCardProduction:
    def test_card_presente(self):
        assert 'data-install-card="production"' in _src()

    def test_titre_production_wsgi(self):
        text = _src()
        assert "Production" in text and "WSGI" in text
        assert "Gunicorn" in text and "reverse proxy" in text

    def test_warn_no_python_app_py_production(self):
        text = _src()
        idx = text.find('data-install-card="production"')
        end = text.find('</section>', idx)
        card_block = text[idx:end]
        normalized = " ".join(card_block.split())
        # La card doit explicitement écarter python app.py / forge run
        # comme parcours de production publique.
        assert "python app.py" in card_block
        assert "forge run" in card_block
        assert (
            "pas d'exposition publique" in normalized
            or "outils de développement" in normalized
        )

    def test_liens_production_complets(self):
        text = _src()
        idx = text.find('data-install-card="production"')
        end = text.find('</section>', idx)
        card_block = text[idx:end]
        # Les 3 guides production doivent être référencés depuis la card.
        assert "forgemvc.com/docs/forge/wsgi-deployment/" in card_block
        assert "forgemvc.com/docs/forge/production-limits/" in card_block
        assert "forgemvc.com/docs/forge/deployment/" in card_block


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
