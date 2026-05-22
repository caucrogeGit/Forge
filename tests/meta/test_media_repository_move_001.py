"""Garde-fou MEDIA-REPOSITORY-MOVE-001.

Vérifie que media_repository et media_gallery ont été déplacés vers
forge_mvc_media, que les shims core ont été supprimés (MEDIA-SHIMS-REMOVE-001),
et que le core ne dépend pas de forge-mvc-media comme dépendance obligatoire.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_REPO = PROJECT_ROOT / "core" / "uploads" / "media_repository.py"
CORE_GALLERY = PROJECT_ROOT / "core" / "uploads" / "media_gallery.py"
OPT_REPO = PROJECT_ROOT / "packages" / "forge-mvc-media" / "forge_mvc_media" / "media_repository.py"
OPT_GALLERY = PROJECT_ROOT / "packages" / "forge-mvc-media" / "forge_mvc_media" / "media_gallery.py"
README = PROJECT_ROOT / "packages" / "forge-mvc-media" / "README.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"


class TestOptInContainsMovedCode:

    def test_media_repository_in_forge_mvc_media(self):
        assert OPT_REPO.exists(), (
            "forge_mvc_media/media_repository.py doit exister dans le package opt-in."
        )

    def test_media_gallery_in_forge_mvc_media(self):
        assert OPT_GALLERY.exists(), (
            "forge_mvc_media/media_gallery.py doit exister dans le package opt-in."
        )

    def test_media_repository_has_sql_logic(self):
        text = OPT_REPO.read_text(encoding="utf-8")
        assert "INSERT INTO media" in text, (
            "forge_mvc_media/media_repository.py doit contenir la logique SQL."
        )

    def test_media_gallery_has_gallery_logic(self):
        text = OPT_GALLERY.read_text(encoding="utf-8")
        assert "get_media_gallery" in text, (
            "forge_mvc_media/media_gallery.py doit contenir la logique de galerie."
        )


class TestCoreFilesAbsent:
    """Les shims de compatibilité ont été supprimés (MEDIA-SHIMS-REMOVE-001)."""

    def test_core_media_repository_shim_removed(self):
        assert not CORE_REPO.exists(), (
            "core/uploads/media_repository.py est présent mais doit être absent. "
            "Ce shim a été supprimé dans MEDIA-SHIMS-REMOVE-001."
        )

    def test_core_media_gallery_shim_removed(self):
        assert not CORE_GALLERY.exists(), (
            "core/uploads/media_gallery.py est présent mais doit être absent. "
            "Ce shim a été supprimé dans MEDIA-SHIMS-REMOVE-001."
        )


class TestCoreDoesNotDependOnOptIn:

    def test_core_init_does_not_unconditionally_import_forge_mvc_media(self):
        text = (PROJECT_ROOT / "core" / "uploads" / "__init__.py").read_text(encoding="utf-8")
        for line in text.splitlines():
            # Les imports indentés (try/except) sont autorisés — seuls les imports
            # directs non indentés constitueraient une dépendance dure.
            if line.startswith("from forge_mvc_media") or line.startswith("import forge_mvc_media"):
                raise AssertionError(
                    "core/uploads/__init__.py ne doit pas importer forge_mvc_media "
                    "directement (sans try/except). "
                    "Les re-exports conditionnels (try/except, indentés) sont autorisés."
                )

    def test_root_pyproject_does_not_depend_on_forge_mvc_media(self):
        lines = ROOT_PYPROJECT.read_text(encoding="utf-8").splitlines()
        active_text = "\n".join(l for l in lines if not l.strip().startswith("#"))
        assert "forge-mvc-media" not in active_text, (
            "Le pyproject.toml racine ne doit pas dépendre de forge-mvc-media "
            "(commentaires exclus de la vérification)."
        )


class TestReadmeAndRoadmap:

    def test_readme_mentions_move_ticket(self):
        assert "MEDIA-REPOSITORY-MOVE-001" in README.read_text(encoding="utf-8"), (
            "Le README de forge-mvc-media doit mentionner MEDIA-REPOSITORY-MOVE-001."
        )

    def test_roadmap_marks_move_as_livré(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "MEDIA-REPOSITORY-MOVE-001" in text, (
            "La roadmap doit mentionner MEDIA-REPOSITORY-MOVE-001."
        )
        idx = text.index("MEDIA-REPOSITORY-MOVE-001")
        bloc = text[idx:idx + 140]
        assert "livré" in bloc, (
            "MEDIA-REPOSITORY-MOVE-001 doit être marqué 'livré' dans la roadmap."
        )
