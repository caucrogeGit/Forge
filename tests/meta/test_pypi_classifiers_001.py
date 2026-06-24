"""Garde-fou PACKAGING-CLASSIFIER-STABLE-001.

Vérifie que les Development Status des pyproject.toml correspondent
à la stratégie documentée dans release-policy.md.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

EXPECTED_CLASSIFIERS = {
    "forge-mvc":          "Development Status :: 4 - Beta",
    "forge-mvc-rbac":     "Development Status :: 4 - Beta",
    "forge-mvc-workflow": "Development Status :: 4 - Beta",
    "forge-mvc-stats":    "Development Status :: 4 - Beta",
    "forge-mvc-mfa":      "Development Status :: 3 - Alpha",
    "forge-mvc-images":   "Development Status :: 3 - Alpha",
    "forge-mvc-iot":      "Development Status :: 3 - Alpha",
    "forge-mvc-video":    "Development Status :: 4 - Beta",
    "forge-mvc-audio":    "Development Status :: 4 - Beta",
    "forge-mvc-files":    "Development Status :: 3 - Alpha",
    "forge-mvc-pivot":    "Development Status :: 4 - Beta",
    "forge-mvc-mail":     "Development Status :: 4 - Beta",
    "forge-mvc-i18n":     "Development Status :: 4 - Beta",
    # forge-mvc-admin : opt-in en cours de construction, non publié (statut Planning).
    "forge-mvc-admin":    "Development Status :: 1 - Planning",
}


def _read_classifier(pyproject_path: Path) -> tuple[str, str | None]:
    """Retourne (project_name, dev_status_classifier)."""
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    name = data["project"]["name"]
    classifiers = data["project"].get("classifiers", [])
    dev_status = next(
        (c for c in classifiers if c.startswith("Development Status")),
        None,
    )
    return name, dev_status


class TestPypiClassifiers:

    def test_all_packages_have_expected_classifier(self):
        """Chaque pyproject.toml doit avoir le classifier prévu."""
        paths = [PROJECT_ROOT / "pyproject.toml"]
        for pkg_dir in (PROJECT_ROOT / "packages").iterdir():
            # forge-mvc-testing : infra de test dev-only, non distribuée (ADR-041).
            if pkg_dir.name == "forge-mvc-testing":
                continue
            if pkg_dir.is_dir() and (pkg_dir / "pyproject.toml").exists():
                paths.append(pkg_dir / "pyproject.toml")

        offenders: list[str] = []
        for path in sorted(paths):
            name, classifier = _read_classifier(path)
            expected = EXPECTED_CLASSIFIERS.get(name)
            if expected is None:
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} : package `{name}` "
                    f"inconnu dans EXPECTED_CLASSIFIERS"
                )
                continue
            if classifier != expected:
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} : `{name}` a "
                    f"{classifier!r}, attendu {expected!r}"
                )

        if offenders:
            raise AssertionError(
                f"{len(offenders)} classifier(s) incohérent(s) :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nVoir docs/release/release-policy.md section "
                + "« Stratégie de classification PyPI »."
            )

    def test_expected_classifiers_match_release_policy(self):
        """La table EXPECTED_CLASSIFIERS doit refléter release-policy.md."""
        policy = (PROJECT_ROOT / "docs" / "release" / "release-policy.md").read_text(
            encoding="utf-8"
        )
        for pkg_name, classifier in EXPECTED_CLASSIFIERS.items():
            status = classifier.split("::")[1].strip()
            if pkg_name not in policy or status not in policy:
                raise AssertionError(
                    f"release-policy.md ne mentionne pas {pkg_name!r} "
                    f"avec status {status!r}"
                )
