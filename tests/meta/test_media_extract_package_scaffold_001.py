"""Garde-fou MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001.

Vérifie que le squelette source-only de forge-mvc-media est correctement
structuré, clairement identifié comme non publié, et ne contient aucun
code applicatif qui aurait dû rester pour le ticket 11.3.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

_CURRENT_VERSION = tomllib.loads((Path(__file__).parent.parent.parent / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGE_DIR = PROJECT_ROOT / "packages" / "forge-mvc-media"
PYPROJECT = PACKAGE_DIR / "pyproject.toml"
README = PACKAGE_DIR / "README.md"
INIT = PACKAGE_DIR / "forge_mvc_media" / "__init__.py"


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


class TestPackageStructure:

    def test_package_dir_exists(self):
        assert PACKAGE_DIR.exists(), "packages/forge-mvc-media/ doit exister."

    def test_pyproject_exists(self):
        assert PYPROJECT.exists(), "packages/forge-mvc-media/pyproject.toml doit exister."

    def test_readme_exists(self):
        assert README.exists(), "packages/forge-mvc-media/README.md doit exister."

    def test_init_exists(self):
        assert INIT.exists(), "packages/forge-mvc-media/forge_mvc_media/__init__.py doit exister."


class TestPackageVersion:

    def test_version_matches_core(self):
        data = _pyproject()
        assert data["project"]["version"] == _CURRENT_VERSION, (
            "forge-mvc-media doit être à la version 1.0.0b4 (synchronisé avec le core)."
        )

    def test_init_version(self):
        text = INIT.read_text(encoding="utf-8")
        assert f'__version__ = "{_CURRENT_VERSION}"' in text, (
            f"forge_mvc_media/__init__.py doit déclarer __version__ = '{_CURRENT_VERSION}'."
        )


class TestPackageClassifier:

    def test_private_do_not_upload_removed(self):
        """MEDIA-PYPI-READY-002 : le classifier privé a été retiré."""
        classifiers = _pyproject()["project"]["classifiers"]
        assert not any("Private :: Do Not Upload" in c for c in classifiers), (
            "forge-mvc-media ne doit plus avoir 'Private :: Do Not Upload' "
            "(retiré dans MEDIA-PYPI-READY-002)."
        )

    def test_not_stable(self):
        classifiers = _pyproject()["project"]["classifiers"]
        assert not any("5 - Production/Stable" in c for c in classifiers), (
            "forge-mvc-media ne doit pas être marqué Production/Stable."
        )

    def test_no_pyotp_dependency(self):
        deps = _pyproject()["project"].get("dependencies", [])
        assert not any("pyotp" in d for d in deps), (
            "forge-mvc-media ne doit pas dépendre de pyotp."
        )


class TestReadmeContent:

    def test_readme_mentions_source_only(self):
        text = README.read_text(encoding="utf-8")
        assert "source-only" in text.lower() or "source only" in text.lower(), (
            "Le README doit mentionner le statut source-only."
        )

    def test_readme_mentions_not_published(self):
        text = README.read_text(encoding="utf-8")
        assert "PyPI" in text, "Le README doit mentionner PyPI (non publié)."
        assert "pas publié" in text.lower() or "non publié" in text.lower() or "not published" in text.lower() or "n'est pas publié" in text.lower(), (
            "Le README doit indiquer que le package n'est pas publié sur PyPI."
        )

    def test_readme_mentions_scaffold_ticket(self):
        assert "MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001" in README.read_text(encoding="utf-8")

    def test_readme_mentions_audit_ticket(self):
        assert "MEDIA-CORE-BOUNDARY-AUDIT-001" in README.read_text(encoding="utf-8")

    def test_readme_mentions_move_ticket(self):
        assert "MEDIA-REPOSITORY-MOVE-001" in README.read_text(encoding="utf-8")


class TestMediaCodePresence:

    def test_media_repository_in_package(self):
        assert (PACKAGE_DIR / "forge_mvc_media" / "media_repository.py").exists(), (
            "media_repository.py doit être dans forge_mvc_media/ "
            "(déplacé par MEDIA-REPOSITORY-MOVE-001)."
        )

    def test_media_gallery_in_package(self):
        assert (PACKAGE_DIR / "forge_mvc_media" / "media_gallery.py").exists(), (
            "media_gallery.py doit être dans forge_mvc_media/ "
            "(déplacé par MEDIA-REPOSITORY-MOVE-001)."
        )

    def test_core_media_repository_is_shim_or_absent(self):
        core_repo = PROJECT_ROOT / "core" / "uploads" / "media_repository.py"
        if core_repo.exists():
            text = core_repo.read_text(encoding="utf-8")
            assert "forge_mvc_media" in text, (
                "core/uploads/media_repository.py existe encore — "
                "il doit être un shim re-exportant depuis forge_mvc_media."
            )

    def test_core_media_gallery_is_shim_or_absent(self):
        core_gallery = PROJECT_ROOT / "core" / "uploads" / "media_gallery.py"
        if core_gallery.exists():
            text = core_gallery.read_text(encoding="utf-8")
            assert "forge_mvc_media" in text, (
                "core/uploads/media_gallery.py existe encore — "
                "il doit être un shim re-exportant depuis forge_mvc_media."
            )


class TestCoreNotDependOnOptIn:

    def test_root_pyproject_does_not_depend_on_forge_mvc_media(self):
        root_pyproject = PROJECT_ROOT / "pyproject.toml"
        lines = root_pyproject.read_text(encoding="utf-8").splitlines()
        active_text = "\n".join(l for l in lines if not l.strip().startswith("#"))
        assert "forge-mvc-media" not in active_text, (
            "Le pyproject.toml racine ne doit pas dépendre de forge-mvc-media "
            "(le core reste indépendant des opt-ins — commentaires exclus de la vérification)."
        )
