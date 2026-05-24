"""Garde-fou CI-OPTIN-MEDIA-BUILD-001.

Verrouille trois propriétés du module opt-in `forge-mvc-media` :

  1. Le packaging existe et est cohérent (nom distribution, nom Python,
     fichiers essentiels).
  2. L'isolation opt-in tient : le core `forge-mvc` n'embarque pas
     `forge-mvc-media` comme dépendance obligatoire ni dans aucun extra.
  3. Le pipeline CI build bien le package opt-in média
     (`.github/workflows/tests.yml`).

Origine : la matrice CI buildait les 4 opt-ins `mfa/rbac/workflow/stats`
mais oubliait silencieusement `forge-mvc-media`. Ce test détecte toute
régression future de la matrice.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
MEDIA_DIR = PROJECT_ROOT / "packages" / "forge-mvc-media"
MEDIA_PYPROJECT = MEDIA_DIR / "pyproject.toml"
MEDIA_README = MEDIA_DIR / "README.md"
MEDIA_PYTHON_PKG = MEDIA_DIR / "forge_mvc_media"
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "tests.yml"


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


# ── 1. Packaging cohérent ───────────────────────────────────────────────────


class TestMediaPackagingExists:
    def test_pyproject_present(self):
        assert MEDIA_PYPROJECT.exists(), (
            f"{MEDIA_PYPROJECT} introuvable — packaging opt-in média cassé."
        )

    def test_readme_present(self):
        assert MEDIA_README.exists()

    def test_python_package_dir_exists(self):
        assert MEDIA_PYTHON_PKG.is_dir(), (
            "Le dossier `forge_mvc_media/` doit exister dans le package."
        )
        assert (MEDIA_PYTHON_PKG / "__init__.py").exists()

    def test_distribution_name(self):
        meta = _load_toml(MEDIA_PYPROJECT)
        assert meta["project"]["name"] == "forge-mvc-media"

    def test_setuptools_includes_python_package(self):
        meta = _load_toml(MEDIA_PYPROJECT)
        include = meta["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any(pat.startswith("forge_mvc_media") for pat in include), (
            f"setuptools doit inclure `forge_mvc_media*`. Trouvé : {include}"
        )


# ── 2. Isolation opt-in : le core ne dépend pas de media ────────────────────


class TestCoreDoesNotRequireMedia:
    def test_core_runtime_deps_exclude_media(self):
        meta = _load_toml(ROOT_PYPROJECT)
        deps = meta["project"].get("dependencies", [])
        offenders = [d for d in deps if "forge-mvc-media" in d.lower()]
        assert not offenders, (
            "forge-mvc-media est un opt-in : il ne doit pas figurer dans "
            f"les dépendances runtime du core. Trouvé : {offenders}"
        )

    def test_core_extras_exclude_media(self):
        meta = _load_toml(ROOT_PYPROJECT)
        extras = meta["project"].get("optional-dependencies", {})
        offenders: dict[str, list[str]] = {}
        for name, items in extras.items():
            hits = [d for d in items if "forge-mvc-media" in d.lower()]
            if hits:
                offenders[name] = hits
        assert not offenders, (
            "forge-mvc-media est volontairement exclu de tous les extras "
            f"du core (cf pyproject.toml). Trouvé : {offenders}"
        )


# ── 3. CI build bien le package opt-in média ────────────────────────────────


class TestCiWorkflowBuildsMedia:
    def test_workflow_file_exists(self):
        assert CI_WORKFLOW.exists(), f"{CI_WORKFLOW} introuvable"

    def test_workflow_lists_media_package_in_optional_builds(self):
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "packages/forge-mvc-media" in content, (
            "La matrice CI doit builder packages/forge-mvc-media dans son "
            "étape `Build optional distributions`. Ajouter le chemin à la "
            "boucle for-pkg du job tests."
        )

    def test_workflow_still_builds_other_optins(self):
        # Sanity : ne pas casser les autres opt-ins en ajoutant le média.
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        for opt in ("forge-mvc-mfa", "forge-mvc-rbac",
                    "forge-mvc-workflow", "forge-mvc-stats"):
            assert f"packages/{opt}" in content, (
                f"packages/{opt} doit rester dans la matrice CI."
            )
