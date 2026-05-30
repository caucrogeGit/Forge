"""Garde-fou OPTIN-PYPI-PUBLISH-PREPARE-001.

Verifie que :
- OPTIN-PYPI-PUBLISH-PREPARE-001 est reference dans la roadmap et marque livré ;
- la dependance forge-mvc est relachee (>=1.0.0b4,<2) dans rbac/workflow/stats ;
- forge-mvc-rbac, workflow, stats n'ont plus 'Private :: Do Not Upload' ;
- forge-mvc-mfa n'a plus 'Private :: Do Not Upload' (requalifié Alpha dans MFA-PYPI-READY-001) ;
- forge-mvc-mfa mentionne SEC-MFA-SECRET-ENCRYPTION-001 dans la doc release-policy ;
- le root pyproject.toml ne depend pas des opt-ins ;
- aucune commande twine upload dist/ n'est recommandee dans release-policy.

Ce test ne fait aucune verification reseau et ne publie rien.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
RELEASE_POLICY = PROJECT_ROOT / "docs" / "release" / "release-policy.md"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_PUBLISHABLE = [
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
]

_ALPHA_PREPARED = [
    "forge-mvc-mfa",
    "forge-mvc-media",
]


class TestRoadmapReference:
    def test_roadmap_mentions_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "OPTIN-PYPI-PUBLISH-PREPARE-001" in text, (
            "La roadmap doit mentionner OPTIN-PYPI-PUBLISH-PREPARE-001."
        )

    def test_roadmap_marks_ticket_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("OPTIN-PYPI-PUBLISH-PREPARE-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "OPTIN-PYPI-PUBLISH-PREPARE-001 doit etre marque 'livré' dans la roadmap."
        )


@pytest.mark.parametrize("pkg", _PUBLISHABLE)
class TestPublishablePackagesDependency:
    def _text(self, pkg: str) -> str:
        toml_path = PROJECT_ROOT / "packages" / pkg / "pyproject.toml"
        return toml_path.read_text(encoding="utf-8")

    def test_dependency_relaxed(self, pkg):
        import tomllib as _toml
        text = self._text(pkg)
        data = _toml.loads(text)
        deps = data.get("project", {}).get("dependencies", [])
        forge_mvc_deps = [d for d in deps if d.startswith("forge-mvc") and ">" in d]
        assert forge_mvc_deps, (
            f"{pkg}/pyproject.toml: la dependance forge-mvc doit etre relachee "
            f"(forge-mvc>=X,<2), pas epinglee a une version fixe avec ==."
        )
        for dep in forge_mvc_deps:
            assert ",<2" in dep, (
                f"{pkg}/pyproject.toml: la contrainte {dep!r} doit avoir une borne superieure <2."
            )

    def test_no_private_do_not_upload(self, pkg):
        text = self._text(pkg)
        assert "Private :: Do Not Upload" not in text, (
            f"{pkg}/pyproject.toml: 'Private :: Do Not Upload' doit etre retire "
            f"pour les packages publiables."
        )


@pytest.mark.parametrize("pkg", _ALPHA_PREPARED)
class TestAlphaPreparedPackages:
    def _text(self, pkg: str) -> str:
        toml_path = PROJECT_ROOT / "packages" / pkg / "pyproject.toml"
        return toml_path.read_text(encoding="utf-8")

    def test_no_private_do_not_upload(self, pkg):
        text = self._text(pkg)
        assert "Private :: Do Not Upload" not in text, (
            f"{pkg}/pyproject.toml: 'Private :: Do Not Upload' doit etre retire "
            f"— ce package a ete requalifie Alpha (MFA-PYPI-READY-001 / MEDIA-PYPI-READY-002)."
        )

    def test_alpha_status(self, pkg):
        import tomllib as _toml
        text = self._text(pkg)
        data = _toml.loads(text)
        classifiers = data.get("project", {}).get("classifiers", [])
        assert any("3 - Alpha" in c for c in classifiers), (
            f"{pkg}: doit avoir 'Development Status :: 3 - Alpha'."
        )


class TestMfaRequiresSecTicket:
    def test_release_policy_mentionne_sec_mfa_ticket(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "release-policy.md doit mentionner SEC-MFA-SECRET-ENCRYPTION-001 "
            "comme prerequis a la publication de forge-mvc-mfa."
        )


class TestRootPyprojectNoMandatoryOptinDeps:
    def _mandatory_deps(self) -> list[str]:
        import tomllib
        data = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))
        return data.get("project", {}).get("dependencies", [])

    @pytest.mark.parametrize("pkg", [
        "forge-mvc-rbac",
        "forge-mvc-workflow",
        "forge-mvc-stats",
        "forge-mvc-media",
        "forge-mvc-mfa",
    ])
    def test_root_pyproject_no_mandatory_dep_on_optin(self, pkg):
        deps = self._mandatory_deps()
        assert not any(pkg in d for d in deps), (
            f"Le pyproject.toml racine ne doit pas avoir {pkg!r} comme dependance obligatoire. "
            f"Les opt-ins sont autorises uniquement dans [project.optional-dependencies]."
        )


class TestNoTwineUploadRecommended:
    def test_release_policy_no_twine_upload_for_optins(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "twine upload dist/forge_mvc_rbac" not in text, (
            "release-policy.md ne doit pas recommander 'twine upload' pour forge-mvc-rbac."
        )

    def test_release_policy_no_twine_upload_for_workflow(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "twine upload dist/forge_mvc_workflow" not in text, (
            "release-policy.md ne doit pas recommander 'twine upload' pour forge-mvc-workflow."
        )

    def test_release_policy_no_twine_upload_for_stats(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "twine upload dist/forge_mvc_stats" not in text, (
            "release-policy.md ne doit pas recommander 'twine upload' pour forge-mvc-stats."
        )
