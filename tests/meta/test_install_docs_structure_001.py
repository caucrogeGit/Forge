"""Tests méta — INSTALL-DOCS-STRUCTURE-001.

Verrouille la nouvelle structure de la section docs/install/ après
réorganisation : les anciennes pages installation-*.md à la racine de
docs/ ont été déplacées sous docs/install/, et un index d'aiguillage
ainsi qu'une entrée production y ont été ajoutés.

Tests :

- les fichiers attendus existent sous docs/install/ ;
- aucun lien actif ne pointe vers les anciens chemins
  (docs/installation-*.md) hors documentation historique ;
- la source landing pointe vers les nouveaux chemins ;
- mkdocs.yml référence la section Installer Forge ;
- mkdocs build --strict passe.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
INSTALL_DIR = PROJECT_ROOT / "docs" / "install"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"
LANDING_SRC = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
DOCS_INDEX_HTML = PROJECT_ROOT / "docs" / "index.html"

EXPECTED_FILES = [
    "index.md",
    "windows-wsl.md",
    "pipx.md",
    "core-dev.md",
    "mariadb.md",
    "vm-debian.md",
    "github.md",
    "windows.md",
    "production.md",
]

# Anciens chemins qui ne doivent plus exister sous docs/ (racine).
OLD_FILES_AT_DOCS_ROOT = [
    "installation.md",
    "installation-pipx.md",
    "installation-developpement.md",
    "installation-mariadb.md",
    "installation-vm-debian.md",
    "installation-windows.md",
    "installation-github.md",
]

# Documentation historique exclue du sweep (mémoire brute — voir CLAUDE.md §9).
HISTORICAL_DIRS = ("docs/history/", "docs/roadmap/", "docs/adr/")
HISTORICAL_FILES = ("CHANGELOG.md",)


class TestInstallDirExists:
    def test_install_dir_exists(self):
        assert INSTALL_DIR.is_dir(), "docs/install/ doit être un répertoire."

    @pytest.mark.parametrize("name", EXPECTED_FILES)
    def test_expected_file_exists(self, name: str):
        path = INSTALL_DIR / name
        assert path.exists(), f"docs/install/{name} doit exister."


class TestIndexIsAiguillage:
    def test_index_titre_explicite(self):
        text = (INSTALL_DIR / "index.md").read_text(encoding="utf-8")
        assert text.startswith("# Installer Forge")

    def test_index_distingue_utilisateur_et_core(self):
        text = (INSTALL_DIR / "index.md").read_text(encoding="utf-8")
        assert "Utilisateur du framework" in text
        assert "Développeur du core" in text

    def test_index_liste_les_parcours(self):
        text = (INSTALL_DIR / "index.md").read_text(encoding="utf-8")
        for link in ("windows-wsl.md", "pipx.md", "core-dev.md",
                     "mariadb.md", "production.md"):
            assert link in text, f"docs/install/index.md doit lier vers {link}."


class TestProductionPage:
    def test_production_page_pointe_vers_pages_existantes(self):
        text = (INSTALL_DIR / "production.md").read_text(encoding="utf-8")
        # Page d'aiguillage courte vers les guides de déploiement existants.
        assert "../deployment/wsgi-deployment.md" in text
        assert "../deployment/production-limits.md" in text
        assert "../deployment/deployment.md" in text

    def test_production_avertit_outils_dev(self):
        text = (INSTALL_DIR / "production.md").read_text(encoding="utf-8")
        assert "python app.py" in text or "forge run" in text


class TestOldFilesRemoved:
    @pytest.mark.parametrize("name", OLD_FILES_AT_DOCS_ROOT)
    def test_old_file_removed(self, name: str):
        path = PROJECT_ROOT / "docs" / name
        assert not path.exists(), (
            f"docs/{name} doit avoir été déplacé sous docs/install/."
        )


class TestNoBrokenInternalLinks:
    """Aucun lien actif n'utilise les anciens chemins installation-*.md."""

    _OLD_LINK_PATTERN = re.compile(
        r"(?<!install/)installation-(?:pipx|developpement|mariadb|"
        r"vm-debian|windows|github)\.md"
    )
    _OLD_INSTALLATION_MD = re.compile(
        r"(?<!\w)installation\.md(?!\w)"
    )

    def _is_historical(self, path: Path) -> bool:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if any(rel.startswith(h) for h in HISTORICAL_DIRS):
            return True
        if rel in HISTORICAL_FILES:
            return True
        return False

    def test_no_old_installation_paths_in_active_md(self):
        offenders: list[str] = []
        for md in PROJECT_ROOT.glob("docs/**/*.md"):
            if self._is_historical(md):
                continue
            text = md.read_text(encoding="utf-8")
            if self._OLD_LINK_PATTERN.search(text):
                offenders.append(md.relative_to(PROJECT_ROOT).as_posix())
        assert not offenders, (
            "Fichiers actifs pointant vers les anciens chemins "
            "installation-*.md :\n  - " + "\n  - ".join(offenders)
        )

    def test_no_old_installation_md_in_active_md(self):
        """Plus aucun lien vers `installation.md` (remplacé par
        `install/index.md`) dans la doc active."""
        offenders: list[str] = []
        for md in PROJECT_ROOT.glob("docs/**/*.md"):
            if self._is_historical(md):
                continue
            text = md.read_text(encoding="utf-8")
            # Ignore mentions de `install/index.md` (le nouveau chemin).
            stripped = text.replace("install/index.md", "")
            if self._OLD_INSTALLATION_MD.search(stripped):
                offenders.append(md.relative_to(PROJECT_ROOT).as_posix())
        assert not offenders, (
            "Fichiers actifs pointant encore vers installation.md :\n  - "
            + "\n  - ".join(offenders)
        )


class TestLandingPointsToNewPaths:
    def test_landing_source_uses_new_install_paths(self):
        text = LANDING_SRC.read_text(encoding="utf-8")
        assert "install/pipx/" in text
        assert "install/core-dev/" in text
        assert "install/windows-wsl/" in text

    def test_landing_source_does_not_reference_old_paths(self):
        text = LANDING_SRC.read_text(encoding="utf-8")
        for old in (
            "installation-pipx/",
            "installation-developpement/",
            "installation-mariadb/",
            "installation-vm-debian/",
            "installation-github/",
            "installation-windows/",
        ):
            assert old not in text, (
                f"Source landing contient encore l'ancien chemin {old}."
            )

    def test_docs_index_html_uses_new_install_paths(self):
        """Si la landing source pointe vers les nouveaux chemins,
        docs/index.html (généré par forge sync:landing) aussi."""
        if not DOCS_INDEX_HTML.exists():
            pytest.skip("docs/index.html absent — lancer `forge sync:landing`.")
        text = DOCS_INDEX_HTML.read_text(encoding="utf-8")
        assert "install/pipx/" in text
        assert "install/core-dev/" in text
        assert "install/windows-wsl/" in text


class TestMkdocsNav:
    def test_section_installer_forge_present(self):
        text = MKDOCS.read_text(encoding="utf-8")
        assert "Installer Forge:" in text

    def test_nav_references_all_install_pages(self):
        text = MKDOCS.read_text(encoding="utf-8")
        for entry in (
            "install/index.md",
            "install/windows-wsl.md",
            "install/pipx.md",
            "install/core-dev.md",
            "install/mariadb.md",
            "install/production.md",
        ):
            assert entry in text, f"mkdocs.yml nav doit inclure {entry}."

    def test_no_old_paths_in_mkdocs_nav(self):
        text = MKDOCS.read_text(encoding="utf-8")
        for old in (
            "installation.md",
            "installation-pipx.md",
            "installation-developpement.md",
            "installation-mariadb.md",
            "installation-vm-debian.md",
            "installation-github.md",
            "installation-windows.md",
        ):
            # STARTERS-WELCOME-INSTALL-001 — on ne vise que les anciennes pages
            # d'install À PLAT (racine de docs/), jamais précédées d'un « / ».
            # Les préambules de parcours `starters/welcome-*/installation.md`
            # portent le même nom de fichier mais sous un sous-dossier (précédés
            # d'un « / ») et restent autorisés.
            flat = re.search(rf"(?<!/){re.escape(old)}", text)
            assert flat is None, (
                f"mkdocs.yml ne doit plus référencer la page plate {old}."
            )


class TestMkdocsBuildStrict:
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
