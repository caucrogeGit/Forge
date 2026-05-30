"""Garde-fou PACKAGE-LOCK-SYNC-001 (option B).

Vérifie que les 7 pyproject.toml sont cohérents entre eux :
1. requires-python aligné (>=3.12 pour tous — ADR-006)
2. Les 6 modules opt-in déclarent forge-mvc comme dépendance directe
3. La version épinglée de forge-mvc dans les modules opt-in correspond
   à la version actuelle de forge-mvc (pin strict `==` ; les pins relâchés
   `>=…,<2` des opt-ins publiables — rbac/workflow/stats/iot — sont ignorés
   par TestVersionAlignment, leur version propre étant vérifiée ailleurs)

Extension PKG-OPTINS-PINNING-POLICY-001 : media et iot, ajoutés après
l'audit F24, sont désormais couverts par OPTIN_MODULES.

Origine : audit F24 — les 4 modules opt-in (mfa, rbac, workflow, stats)
ne déclaraient aucune dépendance vers forge-mvc. Conséquence : pip install
<module-seul> réussissait mais l'import échouait à runtime (forge-mvc non
installé, donc core/ absent). Magie cachée — charte principe 3.

Décision T12 option B : ajouter forge-mvc==X.Y.Z aux 4 pyproject opt-in.

Note R3 : forge-mvc-mfa et forge-mvc-rbac importent core.* directement
(import échoue sans forge-mvc). forge-mvc-workflow et forge-mvc-stats sont
auto-contenus (import réussit), mais la dépendance sémantique reste valide.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
OPTIN_MODULES = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
    "forge-mvc-media",
    "forge-mvc-iot",
]


def _read_pyproject(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _get_version(pyproject_path: Path) -> str:
    data = _read_pyproject(pyproject_path)
    return data["project"]["version"]


def _get_dependencies(pyproject_path: Path) -> list[str]:
    data = _read_pyproject(pyproject_path)
    return data.get("project", {}).get("dependencies", []) or []


def _get_requires_python(pyproject_path: Path) -> str:
    data = _read_pyproject(pyproject_path)
    return data.get("project", {}).get("requires-python", "")


class TestPythonVersionAligned:
    """Tous les pyproject.toml exigent Python >=3.12 (ADR-006)."""

    def test_root_requires_python(self):
        rp = _get_requires_python(ROOT_PYPROJECT)
        assert ">=3.12" in rp, (
            f"pyproject.toml racine doit exiger Python >=3.12 "
            f"(ADR-006), obtenu : {rp!r}"
        )

    @pytest.mark.parametrize("module", OPTIN_MODULES)
    def test_optin_requires_python(self, module: str):
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        rp = _get_requires_python(path)
        assert ">=3.12" in rp, (
            f"{module}/pyproject.toml doit exiger Python >=3.12 "
            f"(ADR-006), obtenu : {rp!r}"
        )


class TestOptinModulesDeclareForgeMvc:
    """Les modules opt-in déclarent forge-mvc comme dépendance directe."""

    @pytest.mark.parametrize("module", OPTIN_MODULES)
    def test_optin_has_forge_mvc_dependency(self, module: str):
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        deps = _get_dependencies(path)
        forge_mvc_deps = [d for d in deps if "forge-mvc" in d]
        assert forge_mvc_deps, (
            f"{module}/pyproject.toml ne déclare pas forge-mvc dans ses "
            f"dependencies. Sans cette déclaration, 'pip install {module}' "
            f"réussit mais l'import échoue (forge-mvc absent). "
            f"Dépendances trouvées : {deps}"
        )


class TestVersionAlignment:
    """La version forge-mvc épinglée dans les modules opt-in correspond
    à la version réelle de forge-mvc."""

    @pytest.mark.parametrize("module", OPTIN_MODULES)
    def test_pinned_version_matches_root(self, module: str):
        root_version = _get_version(ROOT_PYPROJECT)
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        deps = _get_dependencies(path)
        forge_mvc_deps = [d for d in deps if "forge-mvc" in d and "==" in d]
        if not forge_mvc_deps:
            pytest.skip(f"{module} ne déclare pas forge-mvc avec ==")
        for dep in forge_mvc_deps:
            match = re.match(r"forge-mvc==([\d.]+(?:(?:a|b|rc)\d+)?)", dep)
            assert match, (
                f"{module}/pyproject.toml : dépendance forge-mvc mal formée : "
                f"{dep!r}. Format attendu : 'forge-mvc==X.Y.Z[a/b/rcN]'"
            )
            pinned_version = match.group(1)
            assert pinned_version == root_version, (
                f"{module}/pyproject.toml épingle forge-mvc=={pinned_version} "
                f"mais la version racine actuelle est {root_version}. "
                f"Cycle de release manqué — bumper le module aussi."
            )


class TestNoUnnecessaryDuplication:
    """Les modules opt-in ne dupliquent pas les dépendances exclusives du core."""

    CORE_ONLY_DEPS = {
        "mariadb",
        "python-dotenv",
        "jinja2",
        "Pillow",
        "argon2-cffi",
    }

    @pytest.mark.parametrize("module", OPTIN_MODULES)
    def test_optin_does_not_duplicate_core_deps(self, module: str):
        path = PROJECT_ROOT / "packages" / module / "pyproject.toml"
        deps = _get_dependencies(path)
        dep_names = {re.split(r"[<>=!~\[]", d, 1)[0].strip().lower() for d in deps}
        dep_names.discard("forge-mvc")
        duplicates = {
            d for d in dep_names
            if d in {x.lower() for x in self.CORE_ONLY_DEPS}
        }
        assert not duplicates, (
            f"{module}/pyproject.toml duplique des dépendances déjà fournies "
            f"par le core via forge-mvc : {duplicates}. "
            f"À retirer — forge-mvc les apporte transitivement."
        )
