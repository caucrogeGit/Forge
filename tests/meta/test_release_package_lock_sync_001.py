"""Garde-fou RELEASE-PACKAGE-LOCK-SYNC-001.

Verrouille la cohérence des fichiers de packaging côté JavaScript et
empêche le retour d'incohérences de version observées historiquement
(ex. `package-lock.json` resté en `3.0.0` alors que `package.json`
suivait déjà la série `1.0.0-beta.x`).

Le pendant Python (cohérence des 5 `pyproject.toml`, dépendance épinglée
des opt-ins vers `forge-mvc`) reste couvert par
`tests/meta/test_package_lock_sync_001.py` et
`tests/meta/test_packages_optin_no_pypi_001.py`. Ce fichier complète
l'invariant pour la chaîne npm.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGE_JSON = PROJECT_ROOT / "package.json"
PACKAGE_LOCK = PROJECT_ROOT / "package-lock.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ── 1. Cohérence package.json ↔ package-lock.json ───────────────────────────


class TestPackageJsonAndLockAligned:
    def test_both_files_exist(self):
        assert PACKAGE_JSON.exists()
        assert PACKAGE_LOCK.exists()

    def test_package_lock_top_level_version_matches(self):
        pkg = _load(PACKAGE_JSON)
        lock = _load(PACKAGE_LOCK)
        assert lock.get("version") == pkg.get("version"), (
            f"package-lock.json.version ({lock.get('version')!r}) doit "
            f"correspondre à package.json.version ({pkg.get('version')!r}). "
            "Régénérer avec `npm install --package-lock-only`."
        )

    def test_package_lock_root_entry_version_matches(self):
        pkg = _load(PACKAGE_JSON)
        lock = _load(PACKAGE_LOCK)
        # lockfile v3 : packages[""] contient le projet racine.
        root_entry = lock.get("packages", {}).get("", {})
        assert root_entry.get("version") == pkg.get("version"), (
            f"package-lock.json packages[''].version "
            f"({root_entry.get('version')!r}) doit correspondre à "
            f"package.json.version ({pkg.get('version')!r})."
        )

    def test_package_lock_name_matches(self):
        pkg = _load(PACKAGE_JSON)
        lock = _load(PACKAGE_LOCK)
        assert lock.get("name") == pkg.get("name"), (
            f"package-lock.json.name ({lock.get('name')!r}) doit "
            f"correspondre à package.json.name ({pkg.get('name')!r})."
        )


# ── 2. Pas de version legacy 3.0.0 résiduelle ───────────────────────────────


class TestNoLegacyVersionTraces:
    """L'incohérence historique `3.0.0` dans package-lock.json ne doit pas revenir."""

    def test_package_json_does_not_carry_legacy_version(self):
        pkg = _load(PACKAGE_JSON)
        assert pkg.get("version") != "3.0.0"
        assert not (pkg.get("version") or "").startswith("3.")

    def test_package_lock_top_level_not_legacy(self):
        lock = _load(PACKAGE_LOCK)
        assert lock.get("version") != "3.0.0"
        assert not (lock.get("version") or "").startswith("3.")

    def test_package_lock_root_entry_not_legacy(self):
        lock = _load(PACKAGE_LOCK)
        root = lock.get("packages", {}).get("", {})
        assert root.get("version") != "3.0.0"
        assert not (root.get("version") or "").startswith("3.")


# ── 3. Version Forge attendue : série 1.0.0-beta.x ──────────────────────────


class TestForgeVersionSeries:
    """Sanity : la version JavaScript suit la trajectoire 1.0.0-beta.x."""

    def test_package_json_is_in_one_dot_zero_beta_series(self):
        pkg = _load(PACKAGE_JSON)
        version = pkg.get("version", "")
        assert version.startswith("1.0.0"), (
            f"package.json.version ({version!r}) doit être dans la série "
            "1.0.0-beta.x (cf trajectoire officielle Forge)."
        )
