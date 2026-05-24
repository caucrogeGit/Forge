"""Garde-fou SECURITY-CRYPTOGRAPHY-MFA-001.

Verrouille la contrainte `cryptography>=46.0.7,<47` du package opt-in MFA
et l'absence de `cryptography` dans les dépendances runtime du core Forge.

Origine : audit post-publication 1.0.0-beta.8 — la plage `>=42,<46`
embarquait des CVE corrigées en 46.0.7. La nouvelle borne sort de la zone
vulnérable et plafonne sous 47 pour éviter une bascule majeure non testée.

Le core ne doit jamais embarquer `cryptography` : Fernet n'est utilisé que
côté MFA. Si une future modification ajoute la dépendance au core, ce test
échoue immédiatement (régression de l'opt-in).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
MFA_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"

REQUIRED_CONSTRAINT = "cryptography>=46.0.7,<47"


def _project_dependencies(pyproject_path: Path) -> list[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("dependencies", [])


def _optional_dependencies(pyproject_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


class TestMfaCryptographyConstraint:
    def test_mfa_pins_cryptography_to_46_0_7(self):
        deps = _project_dependencies(MFA_PYPROJECT)
        assert REQUIRED_CONSTRAINT in deps, (
            f"forge-mvc-mfa doit déclarer `{REQUIRED_CONSTRAINT}` "
            f"(audit beta.8 — vulnérabilités < 46.0.7). "
            f"Dépendances trouvées : {deps}"
        )


class TestCoreDoesNotShipCryptography:
    def test_core_runtime_excludes_cryptography(self):
        deps = _project_dependencies(ROOT_PYPROJECT)
        offenders = [d for d in deps if d.lower().startswith("cryptography")]
        assert not offenders, (
            "Le core forge-mvc ne doit pas dépendre de `cryptography` — "
            "Fernet est réservé à forge-mvc-mfa (opt-in). "
            f"Trouvé : {offenders}"
        )

    def test_core_extras_exclude_cryptography(self):
        extras = _optional_dependencies(ROOT_PYPROJECT)
        offenders: dict[str, list[str]] = {}
        for name, items in extras.items():
            hits = [d for d in items if d.lower().startswith("cryptography")]
            if hits:
                offenders[name] = hits
        assert not offenders, (
            "Les extras du core ne doivent pas tirer `cryptography` "
            "directement — il vient via forge-mvc-mfa quand l'utilisateur "
            f"installe explicitement le module. Trouvé : {offenders}"
        )
