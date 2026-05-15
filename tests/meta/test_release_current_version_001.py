"""Garde-fou RELEASE-TESTS-CURRENT-VERSION-001.

Vérifie qu'à tout moment, la version courante (lue depuis pyproject.toml
racine) est cohérente partout :
- 4 pyproject.toml opt-in
- forge.py (_FORGE_VERSION + _FORGE_DEFAULT_REF)
- core/__init__.py si __version__ existe
- app.py (docstring d'en-tête)
- CHANGELOG.md : la section de la version courante est datée
- docs/roadmap/forge-roadmap.md : annonce la version courante comme
  ÉTAT COURANT (pas juste une mention historique)
- Tag git vN.Y.Z existe localement (skip si pas créé)
- forge --version retourne la bonne version (skip si forge pas dans le PATH)
- Dépendances internes forge-mvc==N.Y.Z des opt-in pointent vers la version courante

Remplace les anciens tests test_release_3_0_0_stable_001 et
test_release_3_0_2_patch_stable_001 qui codaient la version en dur
et dérivaient à chaque bump.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _current_version() -> str:
    data = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return data["project"]["version"]


def _current_semver() -> str:
    """Version SemVer dérivée de la version PEP 440 (pour tags git et affichage public)."""
    version = _current_version()
    semver = re.sub(r"(\d+\.\d+\.\d+)a(\d+)$", r"\1-alpha.\2", version)
    semver = re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", semver)
    semver = re.sub(r"(\d+\.\d+\.\d+)rc(\d+)$", r"\1-rc.\2", semver)
    return semver


def _semver_tag() -> str:
    return f"v{_current_semver()}"


def _get_pyproject_version(path: Path) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["project"]["version"]


# ---------------------------------------------------------------------------
# Versions cohérentes partout
# ---------------------------------------------------------------------------

class TestAllVersionsBumped:
    """Tous les fichiers de version pointent vers la même version."""

    @pytest.mark.parametrize("module", [
        "forge-mvc-mfa", "forge-mvc-rbac",
        "forge-mvc-workflow", "forge-mvc-stats",
    ])
    def test_optin_module_version(self, module: str):
        expected = _current_version()
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        actual = _get_pyproject_version(path)
        assert actual == expected, (
            f"{module}/pyproject.toml = {actual}, attendu {expected} "
            f"(version racine)"
        )

    @pytest.mark.parametrize("module", [
        "forge-mvc-mfa", "forge-mvc-rbac",
        "forge-mvc-workflow", "forge-mvc-stats",
    ])
    def test_optin_forge_mvc_dependency_version(self, module: str):
        """Chaque module opt-in épingle forge-mvc==<version courante>."""
        expected = _current_version()
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", []) or []
        forge_mvc_deps = [d for d in deps if "forge-mvc==" in d]
        assert forge_mvc_deps, (
            f"{module} ne déclare pas forge-mvc dans dependencies"
        )
        for dep in forge_mvc_deps:
            assert expected in dep, (
                f"{module} : dépendance {dep!r} pas alignée sur "
                f"forge-mvc=={expected}"
            )

    def test_forge_py_version(self):
        expected = _current_version()
        text = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
        match = re.search(r'_FORGE_VERSION\s*=\s*"([^"]+)"', text)
        assert match, "forge.py ne définit pas _FORGE_VERSION"
        assert match.group(1) == expected, (
            f"forge.py _FORGE_VERSION = {match.group(1)!r}, attendu {expected!r}"
        )

    def test_forge_py_default_ref(self):
        expected = _semver_tag()
        text = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
        match = re.search(r'_FORGE_DEFAULT_REF\s*=\s*"([^"]+)"', text)
        assert match, "forge.py ne définit pas _FORGE_DEFAULT_REF"
        assert match.group(1) == expected, (
            f"forge.py _FORGE_DEFAULT_REF = {match.group(1)!r}, attendu {expected!r}"
        )

    def test_core_init_version(self):
        expected = _current_version()
        text = (PROJECT_ROOT / "core" / "__init__.py").read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
        if match:
            assert match.group(1) == expected, (
                f"core/__init__.py __version__ = {match.group(1)!r}, "
                f"attendu {expected!r}"
            )

    def test_app_py_docstring(self):
        semver = _current_semver()
        text = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:5])
        assert f"Forge {semver}" in head, (
            f"app.py docstring ne mentionne pas 'Forge {semver}'."
        )

    def test_root_extras_use_current_version(self):
        """Les extras du pyproject racine pointent vers ==<version courante>."""
        expected = _current_version()
        data = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        extras = data.get("project", {}).get("optional-dependencies", {})
        all_deps = []
        for ext_deps in extras.values():
            all_deps.extend(ext_deps)
        forge_mvc_deps = [d for d in all_deps if "forge-mvc-" in d and "==" in d]
        for dep in forge_mvc_deps:
            match = re.search(r"==(\d+\.\d+\.\d+)", dep)
            assert match, f"Format de dep inattendu : {dep!r}"
            assert match.group(1) == expected, (
                f"Extra dependency {dep!r} pas alignée sur {expected}"
            )


# ---------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------

class TestChangelogDated:
    """La section CHANGELOG de la version courante est datée."""

    def test_current_version_section_has_date(self):
        semver = _current_semver()
        text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        pattern = re.compile(
            rf"## \[{re.escape(semver)}\]\s+[—-]\s+(\d{{4}}-\d{{2}}-\d{{2}})"
        )
        match = pattern.search(text)
        assert match, (
            f"CHANGELOG section [{semver}] doit avoir une date au format "
            f"'## [{semver}] — YYYY-MM-DD'."
        )

    def test_no_unreleased_for_current_version(self):
        semver = _current_semver()
        text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert f"## [{semver}] — Unreleased" not in text, (
            f"CHANGELOG [{semver}] est encore 'Unreleased' alors que la "
            f"release a été faite."
        )


# ---------------------------------------------------------------------------
# Roadmap — vérification renforcée
# ---------------------------------------------------------------------------

class TestRoadmapReflectsCurrentVersion:
    """La roadmap annonce la version courante comme ÉTAT COURANT.

    Renforcement vs ancien test : on exige explicitement un en-tête
    '## État actuel — Forge <version>' et 'Tag courant : `v<version>`',
    plus une assertion négative (aucune version antérieure annoncée comme
    État actuel).
    """

    @property
    def roadmap_text(self) -> str:
        path = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
        if not path.exists():
            pytest.skip("roadmap absente")
        return path.read_text(encoding="utf-8")

    def test_etat_actuel_uses_current_version(self):
        semver = _current_semver()
        text = self.roadmap_text
        pattern = re.compile(
            rf"^##\s+État actuel\s*[—-]\s*Forge\s+{re.escape(semver)}\b",
            re.MULTILINE,
        )
        assert pattern.search(text), (
            f"Roadmap doit contenir '## État actuel — Forge {semver}' "
            f"(version courante en forme SemVer)."
        )

    def test_tag_courant_uses_current_version(self):
        tag = _semver_tag()
        text = self.roadmap_text
        pattern = re.compile(
            rf"Tag courant\s*:\s*`{re.escape(tag)}`"
        )
        assert pattern.search(text), (
            f"Roadmap doit contenir 'Tag courant : `{tag}`'."
        )

    def test_no_older_version_as_etat_actuel(self):
        """Aucune version antérieure ne doit apparaître comme État actuel."""
        semver = _current_semver()
        text = self.roadmap_text
        pattern = re.compile(
            r"^##\s+État actuel\s*[—-]\s*Forge\s+([\d.]+(?:-[\w.]+)?)",
            re.MULTILINE,
        )
        offenders = [
            m.group(0) for m in pattern.finditer(text) if m.group(1) != semver
        ]
        if offenders:
            raise AssertionError(
                "Roadmap contient des en-têtes 'État actuel' avec une "
                f"version différente de la version courante ({semver}) :\n"
                + "\n".join(f"  - {o}" for o in offenders)
            )


# ---------------------------------------------------------------------------
# forge --version
# ---------------------------------------------------------------------------

class TestForgeCommandReturnsCurrentVersion:
    """`forge.py --version` retourne la version courante."""

    def test_forge_version_output(self):
        expected = _current_version()
        try:
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "forge.py"), "--version"],
                capture_output=True, text=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            pytest.skip("forge.py --version timeout")
        output = (result.stdout + result.stderr).strip()
        assert expected in output, (
            f"`forge.py --version` retourne {output!r}, attendu contenant "
            f"'{expected}'."
        )


# ---------------------------------------------------------------------------
# Tag git
# ---------------------------------------------------------------------------

class TestTagExists:
    """Le tag vN.Y.Z existe localement (skip si pas encore créé)."""

    def test_current_version_tag_exists_locally(self):
        version = _current_version()
        tag = f"v{version}"
        try:
            result = subprocess.run(
                ["git", "tag", "-l", tag],
                capture_output=True, text=True, timeout=5,
                cwd=PROJECT_ROOT,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("git non disponible")
        tags = result.stdout.strip().splitlines()
        if not tags:
            pytest.skip(
                f"Tag {tag} non créé encore. "
                f"À créer via : git tag -a {tag} -m '...'"
            )
        assert tag in tags
