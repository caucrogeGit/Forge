"""PROD-DOCTOR-001 — check statique de sécurité production dans `forge doctor`."""
from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from forge_cli import doctor
from forge_cli.doctor import check_prod_security

ROOT = Path(".")


def _cfg(**overrides) -> SimpleNamespace:
    base = {
        "DB_APP_LOGIN": "forge_app",
        "DB_ADMIN_LOGIN": "forge_admin",
        "UPLOAD_MAX_SIZE": 5_242_880,
        "UPLOAD_ALLOWED_EXTENSIONS": "jpg,png,pdf",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestProdSecurity:
    def test_clean_config_is_ok(self):
        assert check_prod_security(ROOT, _cfg()).status == "ok"

    def test_db_no_separation_warns(self):
        r = check_prod_security(ROOT, _cfg(DB_APP_LOGIN="forge_admin"))
        assert r.status == "warn"
        assert "admin" in r.detail.lower()

    def test_unbounded_upload_warns(self):
        assert check_prod_security(ROOT, _cfg(UPLOAD_MAX_SIZE=0)).status == "warn"

    def test_non_numeric_upload_size_warns(self):
        assert check_prod_security(ROOT, _cfg(UPLOAD_MAX_SIZE="x")).status == "warn"

    def test_empty_extensions_warns(self):
        assert check_prod_security(ROOT, _cfg(UPLOAD_ALLOWED_EXTENSIONS="")).status == "warn"

    def test_none_config_skips(self):
        assert check_prod_security(ROOT, None).status == "skip"


class TestIntegration:
    def test_registered_in_run_all(self):
        assert "check_prod_security" in inspect.getsource(doctor.run_all)
