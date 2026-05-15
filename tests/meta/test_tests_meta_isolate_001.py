"""Garde-fou TESTS-META-ISOLATE-001.

Vérifie que chaque fichier dans tests/meta/ utilise le marker `pytest.mark.meta`
pour permettre la séparation entre tests fonctionnels et tests de cohérence
projet (charte 3.E).

Sans ce garde-fou, un développeur peut ajouter un fichier dans tests/meta/
sans le marker, et son test sera lancé dans la suite par défaut même quand on
veut filtrer avec `-m "not meta"`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

META_DIR = Path(__file__).parent


def _meta_test_files() -> list[Path]:
    return sorted(META_DIR.glob("test_*.py"))


class TestAllMetaFilesAreMarked:
    """Chaque fichier tests/meta/test_*.py utilise pytestmark = pytest.mark.meta."""

    def test_meta_dir_exists(self):
        assert META_DIR.exists()

    def test_at_least_some_meta_files(self):
        files = _meta_test_files()
        assert len(files) >= 20, (
            f"tests/meta/ ne contient que {len(files)} fichier(s). "
            "Vérifier le chemin."
        )

    def test_each_file_has_pytestmark_meta(self):
        missing: list[str] = []
        patterns = [
            r"^pytestmark\s*=\s*pytest\.mark\.meta\b",
            r"^pytestmark\s*=\s*\[.*pytest\.mark\.meta.*\]",
        ]
        for f in _meta_test_files():
            text = f.read_text(encoding="utf-8")
            found = any(re.search(p, text, re.MULTILINE) for p in patterns)
            if not found:
                missing.append(f.name)

        assert not missing, (
            f"{len(missing)} fichier(s) dans tests/meta/ sans "
            "`pytestmark = pytest.mark.meta` :\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nAjouter après les imports :\n  pytestmark = pytest.mark.meta"
        )


class TestMarkerDeclaredInConfig:
    """Le marker `meta` est déclaré dans la config pytest."""

    def test_marker_declared_in_pytest_ini(self):
        ini = Path("pytest.ini")
        assert ini.exists(), "pytest.ini doit exister."
        text = ini.read_text(encoding="utf-8")
        assert re.search(r"^\s*meta\s*:", text, re.MULTILINE), (
            "Le marker `meta` n'est pas déclaré dans pytest.ini. "
            "Ajouter sous [pytest] :\n"
            "  markers =\n"
            "      meta: test de cohérence projet — pas un test fonctionnel"
        )
