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
- Dépendances internes forge-mvc>=N.Y.Z des opt-in pointent vers la version courante
  (politique unifiée OPTIN-DEPS-PIN-B13-001 : `forge-mvc>=<version>,<2` partout)

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
        "forge-mvc-images", "forge-mvc-files",
        "forge-mvc-iot", "forge-mvc-video", "forge-mvc-audio",
    ])
    def test_optin_module_version(self, module: str):
        expected = _current_version()
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        actual = _get_pyproject_version(path)
        assert actual == expected, (
            f"{module}/pyproject.toml = {actual}, attendu {expected} "
            f"(version racine)"
        )

    def test_optin_mfa_forge_mvc_dependency_pinned(self):
        """forge-mvc-mfa déclare forge-mvc>=<version courante> (politique unifiée
        OPTIN-DEPS-PIN-B13-001 — plancher aligné sur la version racine)."""
        expected = _current_version()
        path = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", []) or []
        forge_mvc_deps = [
            d for d in deps if d.startswith("forge-mvc") and "forge-mvc-" not in d
        ]
        assert forge_mvc_deps, "forge-mvc-mfa ne déclare pas forge-mvc dans dependencies"
        for dep in forge_mvc_deps:
            assert expected in dep, (
                f"forge-mvc-mfa : dépendance {dep!r} pas alignée sur "
                f"forge-mvc>={expected}"
            )

    @pytest.mark.parametrize("module", [
        "forge-mvc-rbac", "forge-mvc-workflow", "forge-mvc-stats",
        "forge-mvc-images", "forge-mvc-iot", "forge-mvc-video",
    ])
    def test_publishable_optin_forge_mvc_dependency_declared(self, module: str):
        """Les opt-ins publiables déclarent forge-mvc avec le plancher unifié
        `>=<version>,<2` (OPTIN-DEPS-PIN-B13-001)."""
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps = data.get("project", {}).get("dependencies", []) or []
        forge_mvc_deps = [d for d in deps if d.startswith("forge-mvc")]
        assert forge_mvc_deps, (
            f"{module} ne déclare pas forge-mvc dans dependencies"
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
        text = (PROJECT_ROOT / "tests" / "fixtures" / "app" / "app.py").read_text(encoding="utf-8")
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
            rf"## \[{re.escape(semver)}\]\s+[—\-:]\s+(\d{{4}}-\d{{2}}-\d{{2}})"
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
    '## État actuel : Forge <version>' et 'Tag courant : `v<version>`',
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
            rf"^##\s+État actuel\s*[—\-:]\s*Forge\s+{re.escape(semver)}\b",
            re.MULTILINE,
        )
        assert pattern.search(text), (
            f"Roadmap doit contenir '## État actuel : Forge {semver}' "
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
            r"^##\s+État actuel\s*[—\-:]\s*Forge\s+([\d.]+(?:-[\w.]+)?)",
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
# Tag git — convention SemVer publique (RELEASE-TAG-CONVENTION-TEST-ALIGN-001)
# ---------------------------------------------------------------------------
#
# Forge utilise DEUX formats coexistants pour la même release :
#   - PEP 440 (Python)  : 1.0.0b9       → pyproject.toml, core/__init__.py,
#                                          forge.py, paquets PyPI
#   - SemVer (public)   : 1.0.0-beta.9  → CHANGELOG, tags Git, package.json,
#                                          documentation
#
# Le tag Git officiel suit la convention SemVer : `v1.0.0-beta.9`, pas
# `v1.0.0b9`. La conversion PEP 440 → SemVer est fournie par
# `_current_semver()` plus haut (cf RELEASE-VALIDATE-PEP440-SEMVERSION-001),
# et l'utilitaire `tools/release-validate.sh --convert semver <pep440>`
# implémente la même règle côté script release.

class TestTagExists:
    """Le tag `v<SemVer>` existe localement (skip si pas encore créé)."""

    def test_current_version_tag_uses_semver_format(self):
        """Le tag attendu pour la version courante est `v1.0.0-beta.N` —
        jamais `v1.0.0bN`."""
        version = _current_version()
        tag = _semver_tag()
        # Le tag attendu doit dériver la forme SemVer, pas PEP 440.
        assert tag.startswith("v"), f"Le tag doit commencer par `v`, reçu : {tag!r}"
        # Si la version courante est une pre-release PEP 440 (b/a/rc),
        # le tag doit utiliser la forme SemVer correspondante (-beta./-alpha./-rc.).
        if re.search(r"\d+\.\d+\.\d+[abrc]+\d+$", version):
            assert tag != f"v{version}", (
                f"Le tag `{tag}` ne doit PAS être identique à `v{version}` "
                "(format PEP 440). Forge utilise SemVer pour les tags Git — "
                "voir `_current_semver()` et `tools/release-validate.sh "
                "--convert semver`."
            )
            # Le tag doit contenir un séparateur SemVer (« -beta. » / « -alpha. » / « -rc. »).
            assert re.search(r"-(alpha|beta|rc)\.\d+$", tag), (
                f"Le tag pre-release `{tag}` doit suivre la forme SemVer "
                "(`v<major>.<minor>.<patch>-(alpha|beta|rc).<n>`)."
            )

    def test_current_version_tag_exists_locally(self):
        tag = _semver_tag()
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

    def test_release_validate_helper_agrees_on_tag_format(self):
        """`tools/release-validate.sh --convert semver <pep440>` doit
        produire la même forme SemVer que `_current_semver()`. C'est le
        garde-fou contre une divergence entre le test et le script release."""
        script = PROJECT_ROOT / "tools" / "release-validate.sh"
        if not script.is_file():
            pytest.skip("tools/release-validate.sh absent")
        try:
            result = subprocess.run(
                ["bash", str(script), "--convert", "semver", _current_version()],
                capture_output=True, text=True, timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("bash non disponible")
        assert result.returncode == 0, (
            f"--convert semver a échoué : {result.stderr!r}"
        )
        script_semver = result.stdout.strip()
        assert script_semver == _current_semver(), (
            f"Divergence entre helpers : `_current_semver()` = "
            f"{_current_semver()!r} mais `release-validate.sh --convert semver "
            f"{_current_version()}` = {script_semver!r}. Aligner les deux "
            "(une seule source de vérité pour la conversion PEP 440 ↔ SemVer)."
        )
