"""Tests documentaires — INSTALL-WSL-DOCS-001 (refonte page légère).

Depuis la refonte, `docs/install/windows-wsl.md` ne documente plus
l'installation complète de Forge : elle **prépare WSL2/Ubuntu** puis
**délègue** à la procédure Linux (`poste-linux.md`).

Le contenu d'installation proprement dit a migré :
- installation de Forge (pipx, forge new, forge run) → `poste-linux.md` ;
- comptes MariaDB / `forge_admin` / SQL → `mariadb-comptes.md`
  (gardé par `test_install_mariadb_comptes_001.py`).

Ce test verrouille donc le périmètre de la page légère et sa délégation,
pas les détails d'installation.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

DOC = Path("docs/install/windows-wsl.md")
MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


class TestExistence:
    def test_fichier_existe(self):
        assert DOC.exists(), "docs/install/windows-wsl.md introuvable."

    def test_fichier_substantiel(self):
        assert len(_text()) > 1_500

    def test_titre_h1_correct(self):
        first_h1 = next(
            line for line in _text().splitlines() if line.startswith("# ")
        )
        assert "WSL" in first_h1 and "Windows" in first_h1


class TestPreparationWSL:
    def test_commande_install_wsl(self):
        assert "wsl --install -d Ubuntu-24.04" in _text()

    def test_mentionne_ubuntu_24_04(self):
        text = _text()
        assert "Ubuntu 24.04" in text or "Ubuntu-24.04" in text


class TestSystemeFichiersLinux:
    def test_recommande_le_home_linux(self):
        """La convention de dossier utilisateur est `~/Projets/`."""
        assert "~/Projets" in _text()

    def test_ne_recommande_plus_dev(self):
        """L'ancienne convention `~/dev/` a été remplacée par `~/Projets/`."""
        assert "~/dev" not in _text(), (
            "La page ne doit plus mentionner `~/dev` (convention "
            "remplacée par `~/Projets`)."
        )

    def test_avertit_contre_mnt_c(self):
        assert "/mnt/c" in _text()


class TestVsCode:
    def test_mentionne_extension_wsl(self):
        assert "ms-vscode-remote.remote-wsl" in _text()


class TestDelegation:
    """La page prépare WSL puis délègue à la procédure Linux."""

    def test_delegue_vers_poste_linux(self):
        assert "poste-linux.md" in _text()

    def test_renvoie_vers_depannage_wsl(self):
        assert "wsl-dev-server.md" in _text()

    def test_n_installe_pas_forge_elle_meme(self):
        """Le détail d'installation a migré : la page ne doit pas réintroduire
        la commande pipx canonique ni la création de comptes MariaDB."""
        text = _text()
        assert 'pipx install --pip-args="--pre" forge-mvc' not in text
        assert "CREATE USER" not in text


class TestMkdocs:
    def test_nav_reference_la_page(self):
        assert "install/windows-wsl.md" in MKDOCS.read_text(encoding="utf-8")

    def test_libelle_nav(self):
        assert "Windows + WSL" in MKDOCS.read_text(encoding="utf-8")

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


class TestRoadmap:
    def test_ticket_present(self):
        assert "INSTALL-WSL-DOCS-001" in ROADMAP.read_text(encoding="utf-8")

    def test_ticket_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "INSTALL-WSL-DOCS-001" in line:
                assert "livré" in line.lower(), (
                    f"INSTALL-WSL-DOCS-001 non marqué comme livré : {line}"
                )
                return
        pytest.fail("Ligne INSTALL-WSL-DOCS-001 introuvable.")
