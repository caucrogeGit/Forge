"""Garde-fou SECURITY-CRYPTOGRAPHY-MFA-001.

Verrouille la contrainte `cryptography>=50.0.0,<51` du package opt-in MFA
et l'absence de `cryptography` dans les dépendances runtime du core Forge.

Origine : audit post-publication 1.0.0-beta.8 — la plage `>=42,<46` embarquait
des CVE corrigées en 46.0.7 ; la borne avait été fixée à `>=46.0.7,<47` (sous le
major 47 non testé). Audit ultérieur : `GHSA-537c-gmf6-5ccf` vise l'OpenSSL lié
statiquement dans les wheels cryptography antérieures à 48.0.1, corrigé en
48.0.1 ; le plancher est passé à `>=48.0.1`, plafonné sous le major 49.

`DEPS-CRYPTOGRAPHY-50-001` (2026-08-04) : trois avis publiés le même jour visent
la 48.0.1, et la CI de `main` est passée au rouge en quelques heures.

- `CVE-2026-69248`, contournement de contraintes de noms X.509 : une CA
  intermédiaire limitée à `foo.example.com` accepte une feuille portant le
  joker `*.example.com`, ce qui sort du périmètre autorisé. Corrigé en 49.0.0.
- `CVE-2026-69249`, explosion exponentielle sur une chaîne invalide contenant
  des copies d'un même certificat auto-signé. Corrigé en 49.0.0.
- `CVE-2026-69247`, oracle de déchiffrement PKCS#7 : l'issue du déchiffrement
  d'un `encryptedKey` était distinguable et révélait la longueur récupérée de
  l'opération RSA. Corrigé en **50.0.0** seulement, d'où ce plancher.

Aucun des trois ne touche le chemin de Forge, qui n'utilise que
`cryptography.fernet.Fernet`, du chiffrement symétrique, sans X.509 ni PKCS#7.
La borne monte quand même : la dépendance est **expédiée** avec l'opt-in, et une
application peut s'en servir pour tout autre chose.

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

REQUIRED_CONSTRAINT = "cryptography>=50.0.0,<51"


def _project_dependencies(pyproject_path: Path) -> list[str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("dependencies", [])


def _optional_dependencies(pyproject_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


class TestMfaCryptographyConstraint:
    def test_mfa_pins_cryptography_secure_range(self):
        deps = _project_dependencies(MFA_PYPROJECT)
        assert REQUIRED_CONSTRAINT in deps, (
            f"forge-mvc-mfa doit déclarer `{REQUIRED_CONSTRAINT}` "
            f"(CVE-2026-69247 sur PKCS#7, corrigé en 50.0.0 seulement). "
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
