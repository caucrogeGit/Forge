"""Garde-fou DOCTOR-SECURITY-OPTIN-001.

Recadre MFA et RBAC dans le doctor comme des gardes-fous *fail-open* de
sécurité (et non un inventaire d'opt-in) :

- les labels MFA et RBAC portent la mention « sécurité », pas « opt-in » ;
- check_rbac_dependency est exposée, symétrique de check_mfa_dependency ;
- la détection RBAC ne s'appuie que sur des signaux non ambigus (contrat
  mvc/security/rbac.json, import forge_mvc_rbac) — pas sur un mot-clé de nom de
  fichier qui produirait des faux positifs sur les starters welcome-rbac ;
- le check RBAC est branché dans run_all ;
- doctor.py utilise find_spec, pas un import direct de forge_mvc_rbac.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCTOR_PY = PROJECT_ROOT / "cli" / "project" / "doctor.py"


# ---------------------------------------------------------------------------
# Labels « sécurité » — MFA et RBAC ne se présentent plus comme « opt-in »
# ---------------------------------------------------------------------------

class TestSecurityLabels:

    def test_mfa_label_is_security_not_optin(self, tmp_path):
        from cli.project.doctor import check_mfa_dependency
        result = check_mfa_dependency(tmp_path)
        assert result.label == "MFA (sécurité)"

    def test_rbac_label_is_security(self, tmp_path):
        from cli.project.doctor import check_rbac_dependency
        result = check_rbac_dependency(tmp_path)
        assert result.label == "RBAC (sécurité)"

    def test_no_mfa_optin_label_in_source(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "MFA (opt-in)" not in src, (
            "Le label MFA doit être recadré « sécurité », pas « opt-in »"
        )


# ---------------------------------------------------------------------------
# check_rbac_dependency exposée et symétrique de MFA
# ---------------------------------------------------------------------------

class TestCheckRbacDependencyExposed:

    def test_check_rbac_dependency_importable(self):
        from cli.project.doctor import check_rbac_dependency
        assert callable(check_rbac_dependency)

    def test_detect_rbac_indicators_importable(self):
        from cli.project.doctor import _detect_rbac_indicators
        assert callable(_detect_rbac_indicators)


# ---------------------------------------------------------------------------
# Détection RBAC — signaux non ambigus uniquement
# ---------------------------------------------------------------------------

class TestDetectRbacIndicators:

    def test_no_signs_returns_empty(self, tmp_path):
        (tmp_path / "mvc").mkdir()
        assert _read("_detect_rbac_indicators")(tmp_path) == []

    def test_contract_file_detected(self, tmp_path):
        contract = tmp_path / "mvc" / "security" / "rbac.json"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text("{}\n", encoding="utf-8")
        indicators = _read("_detect_rbac_indicators")(tmp_path)
        assert any("rbac.json" in i for i in indicators)

    def test_import_detected(self, tmp_path):
        ctrl = tmp_path / "mvc" / "controllers" / "admin_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text(
            "from forge_mvc_rbac import require_contract_permission\n",
            encoding="utf-8",
        )
        indicators = _read("_detect_rbac_indicators")(tmp_path)
        assert any("import RBAC" in i for i in indicators)

    def test_rbac_keyword_filename_is_not_an_indicator(self, tmp_path):
        """Un nom de fichier contenant « rbac » sans import ni contrat ne doit
        PAS être détecté (faux positif welcome-rbac)."""
        ctrl = tmp_path / "mvc" / "controllers" / "rbac_role_controller.py"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("def index(request):\n    return None\n", encoding="utf-8")
        assert _read("_detect_rbac_indicators")(tmp_path) == []


# ---------------------------------------------------------------------------
# check_rbac_dependency — skip / warn fail-open
# ---------------------------------------------------------------------------

class TestCheckRbacDependency:

    def test_skip_when_no_rbac_indicators(self, tmp_path):
        from cli.project.doctor import check_rbac_dependency
        result = check_rbac_dependency(tmp_path)
        assert result.status == "skip"
        assert "aucun indice RBAC" in result.detail

    def test_warn_when_rbac_used_but_module_absent(self, tmp_path):
        from cli.project.doctor import check_rbac_dependency
        contract = tmp_path / "mvc" / "security" / "rbac.json"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text("{}\n", encoding="utf-8")

        import cli.project.doctor as _doctor
        orig = _doctor.importlib.util.find_spec
        _doctor.importlib.util.find_spec = lambda name: None
        try:
            result = check_rbac_dependency(tmp_path)
        finally:
            _doctor.importlib.util.find_spec = orig

        assert result.status == "warn"
        assert result.status != "fail", "Le warning RBAC ne doit pas être bloquant"
        assert "forge_mvc_rbac" in result.detail
        assert "opt-in" in result.detail or "source-only" in result.detail


# ---------------------------------------------------------------------------
# Branchement et frontière d'import
# ---------------------------------------------------------------------------

class TestDoctorWiringAndBoundary:

    def test_check_rbac_dependency_in_run_all(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "check_rbac_dependency(root)" in src, (
            "check_rbac_dependency doit être appelé dans run_all de doctor.py"
        )

    def test_doctor_uses_find_spec_for_rbac(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert 'find_spec("forge_mvc_rbac")' in src, (
            "doctor.py doit utiliser find_spec pour détecter forge_mvc_rbac"
        )

    def test_doctor_does_not_import_forge_mvc_rbac_at_module_level(self):
        src = DOCTOR_PY.read_text(encoding="utf-8")
        assert "import forge_mvc_rbac" not in src, (
            "doctor.py ne doit pas importer forge_mvc_rbac au niveau module"
        )


def _read(name):
    """Importe paresseusement un symbole de cli.project.doctor par son nom."""
    import cli.project.doctor as _doctor
    return getattr(_doctor, name)
