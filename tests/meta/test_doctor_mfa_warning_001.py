"""Garde-fou AUTH-DOCTOR-MFA-MISSING-DEP-WARNING-001.

Vérifie que :
- check_mfa_dependency est exportée par cli.project.doctor.
- Le message de warning mentionne MFA comme opt-in/source-only.
- pyotp n'est pas dans les dépendances runtime du core (pyproject.toml).
- pyotp n'est pas dans requirements*.txt du core.
- core/ ne contient pas d'import pyotp (complète test_core_optin_import_boundary_001).
- Le code doctor utilise find_spec, pas un import direct.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOCTOR_PY = PROJECT_ROOT / "cli" / "project" / "doctor.py"


# ---------------------------------------------------------------------------
# check_mfa_dependency est exposée
# ---------------------------------------------------------------------------

class TestCheckMfaDependencyExposed:

    def test_check_mfa_dependency_importable(self):
        from cli.project.doctor import check_mfa_dependency
        assert callable(check_mfa_dependency)

    def test_detect_mfa_indicators_importable(self):
        from cli.project.doctor import _detect_mfa_indicators
        assert callable(_detect_mfa_indicators)


# ---------------------------------------------------------------------------
# Message doctor — qualité du warning
# ---------------------------------------------------------------------------

class TestDoctorMfaWarningMessage:

    def test_doctor_mentions_opt_in_in_warn(self, tmp_path):
        from cli.project.doctor import check_mfa_dependency
        ctrl = tmp_path / "mvc" / "controllers" / "mfa_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("# mfa\n", encoding="utf-8")

        import importlib.util as _iutil

        original_find = _iutil.find_spec

        def patched(name):
            if name == "forge_mvc_mfa":
                return None
            return original_find(name)

        import cli.project.doctor as _doctor
        orig = _doctor.importlib.util.find_spec
        _doctor.importlib.util.find_spec = patched
        try:
            result = check_mfa_dependency(tmp_path)
        finally:
            _doctor.importlib.util.find_spec = orig

        assert result.status == "warn"
        assert "opt-in" in result.detail or "source-only" in result.detail, (
            "Le message doctor MFA doit mentionner que MFA est opt-in ou source-only"
        )

    def test_doctor_mfa_warn_mentions_forge_mvc_mfa(self, tmp_path):
        from cli.project.doctor import check_mfa_dependency
        ctrl = tmp_path / "mvc" / "controllers" / "mfa_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("# mfa\n", encoding="utf-8")

        import cli.project.doctor as _doctor
        orig = _doctor.importlib.util.find_spec
        _doctor.importlib.util.find_spec = lambda name: None
        try:
            result = check_mfa_dependency(tmp_path)
        finally:
            _doctor.importlib.util.find_spec = orig

        assert "forge_mvc_mfa" in result.detail, (
            "Le message doctor MFA doit mentionner forge_mvc_mfa"
        )

    def test_doctor_mfa_warn_is_not_fail(self, tmp_path):
        from cli.project.doctor import check_mfa_dependency
        ctrl = tmp_path / "mvc" / "controllers" / "mfa_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("# mfa\n", encoding="utf-8")

        import cli.project.doctor as _doctor
        orig = _doctor.importlib.util.find_spec
        _doctor.importlib.util.find_spec = lambda name: None
        try:
            result = check_mfa_dependency(tmp_path)
        finally:
            _doctor.importlib.util.find_spec = orig

        assert result.status != "fail", (
            "Le warning MFA doctor ne doit pas être un FAIL (non bloquant)"
        )


# ---------------------------------------------------------------------------
# pyotp absent des dépendances core
# ---------------------------------------------------------------------------

class TestPyotpNotInCoreDeps:
    """`pyotp` n'est pas une dépendance du cœur.

    Ces contrôles cherchaient la **chaîne** `pyotp` n'importe où dans le
    fichier. Ils figeaient le moyen, pas la fin qu'ils énoncent eux mêmes,
    « pas dans les dépendances runtime du core »
    (`PKG-PYRIGHT-FIXTURES-001`, relecture du pyproject racine).

    Conséquence : le fichier ne pouvait pas **expliquer** pourquoi
    `forge-mvc-mfa` est hors de l'extra `all`, alors que nommer ce qu'un opt-in
    tire avec lui est la seule raison durable de l'en écarter. Un commentaire
    qui dit « mfa tire pyotp » faisait échouer un test qui vise les
    dépendances.
    """

    def _dependances(self) -> "set[str]":
        """Toutes les dépendances déclarées, extras compris, en minuscules."""
        import tomllib

        projet = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
        declarees = list(projet.get("dependencies", []))
        for extra in projet.get("optional-dependencies", {}).values():
            declarees.extend(extra)
        return {d.lower() for d in declarees}

    def test_pyotp_not_in_pyproject_dependencies(self):
        fautives = [d for d in self._dependances() if "pyotp" in d]

        assert not fautives, (
            f"pyotp ne doit pas être une dépendance du core forge-mvc : "
            f"{', '.join(fautives)}. Il appartient à forge-mvc-mfa, qui le "
            f"déclare lui-même."
        )

    def test_requirements_txt_exists_or_skip(self):
        req = PROJECT_ROOT / "requirements.txt"
        if not req.exists():
            pytest.skip("requirements.txt absent — pas de dépendances runtime listées")
        lignes = [
            ligne.split("#", 1)[0].strip()
            for ligne in req.read_text(encoding="utf-8").splitlines()
        ]
        fautives = [ligne for ligne in lignes if ligne and "pyotp" in ligne.lower()]

        assert not fautives, (
            f"pyotp ne doit pas être une exigence du core : {', '.join(fautives)}"
        )


# ---------------------------------------------------------------------------
# doctor.py utilise find_spec, pas un import direct de forge_mvc_mfa
# ---------------------------------------------------------------------------

class TestDoctorUsesFinspec:

    def test_doctor_uses_find_spec_for_mfa(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "find_spec" in src, (
            "cli/project/doctor.py doit utiliser importlib.util.find_spec pour détecter MFA"
        )

    def test_doctor_does_not_import_forge_mvc_mfa_at_module_level(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "import forge_mvc_mfa" not in src, (
            "cli/project/doctor.py ne doit pas importer forge_mvc_mfa au niveau module"
        )

    def test_doctor_does_not_import_pyotp_at_module_level(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "import pyotp" not in src, (
            "cli/project/doctor.py ne doit pas importer pyotp au niveau module"
        )

    def test_check_mfa_dependency_in_run_all(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "check_mfa_dependency" in src, (
            "check_mfa_dependency doit être appelé dans run_all de doctor.py"
        )
