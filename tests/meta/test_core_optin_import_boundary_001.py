"""Garde-fou AUTH-AUDIT-VOCAB-PERIMETER-001 — frontière d'import core / opt-ins.

Vérifie que core/ ne contient aucun import de forge_mvc_mfa, forge_mvc_rbac
ou pyotp.

Ces imports sont légitimes dans packages/, tests/ et docs/, mais interdits
dans le core (ADR-004, ADR-011).

La vérification est textuelle (lecture du source Python), pas basée sur
importlib, pour rester indépendante de l'environnement d'installation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_ROOT = PROJECT_ROOT / "core"

_FORBIDDEN_IMPORTS = [
    "forge_mvc_mfa",
    "forge_mvc_rbac",
    "pyotp",
]

_IMPORT_RE = re.compile(
    r"^\s*(import|from)\s+(forge_mvc_mfa|forge_mvc_rbac|pyotp)",
    re.MULTILINE,
)


def _collect_core_py_files() -> list[Path]:
    return [
        p for p in CORE_ROOT.rglob("*.py")
        if "__pycache__" not in str(p)
    ]


def _violations() -> list[tuple[Path, str]]:
    """Retourne (fichier, ligne) pour chaque import interdit dans core/."""
    found = []
    for path in _collect_core_py_files():
        src = path.read_text(encoding="utf-8")
        for match in _IMPORT_RE.finditer(src):
            line = src[: match.start()].count("\n") + 1
            found.append((path.relative_to(PROJECT_ROOT), f"ligne {line}: {match.group().strip()}"))
    return found


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCoreOptinImportBoundary:

    def test_core_does_not_import_forge_mvc_mfa(self):
        violations = [
            f"{path} — {line}"
            for path, line in _violations()
            if "forge_mvc_mfa" in line
        ]
        assert not violations, (
            "core/ ne doit pas importer forge_mvc_mfa (ADR-011) :\n"
            + "\n".join(violations)
        )

    def test_core_does_not_import_forge_mvc_rbac(self):
        violations = [
            f"{path} — {line}"
            for path, line in _violations()
            if "forge_mvc_rbac" in line
        ]
        assert not violations, (
            "core/ ne doit pas importer forge_mvc_rbac (ADR-011) :\n"
            + "\n".join(violations)
        )

    def test_core_does_not_import_pyotp(self):
        violations = [
            f"{path} — {line}"
            for path, line in _violations()
            if "pyotp" in line
        ]
        assert not violations, (
            "core/ ne doit pas importer pyotp (ADR-011) :\n"
            + "\n".join(violations)
        )

    def test_no_violations_at_all(self):
        violations = _violations()
        assert not violations, (
            "core/ contient des imports opt-in interdits (ADR-011) :\n"
            + "\n".join(f"{p} — {l}" for p, l in violations)
        )

    def test_core_py_files_scanned(self):
        files = _collect_core_py_files()
        assert len(files) > 10, (
            f"Seulement {len(files)} fichiers .py trouvés dans core/ — "
            "vérifier que le scan fonctionne correctement"
        )
