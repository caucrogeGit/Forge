"""PROD-DOCTOR-001 — check statique de sécurité production dans `forge doctor`."""
from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli.project import doctor
from cli.project.doctor import check_prod_security

ROOT = Path(".")


def _cfg(**overrides) -> SimpleNamespace:
    # ADR-032 : check_prod_security ne lit plus UPLOAD_ALLOWED_EXTENSIONS depuis
    # l'objet config mais depuis os.environ (la liste appartient à l'opt-in
    # forge-mvc-files). Seuls les logins DB et UPLOAD_MAX_SIZE restent sur config.
    base = {
        "DB_APP_LOGIN": "forge_app",
        "DB_ADMIN_LOGIN": "forge_admin",
        "UPLOAD_MAX_SIZE": 5_242_880,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def _restrictive_extensions_env(monkeypatch):
    """Par défaut, UPLOAD_ALLOWED_EXTENSIONS non vide : pas d'avertissement
    d'extensions. Les tests qui veulent le déclencher vident la variable."""
    monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", "jpg,png,pdf")


class TestProdSecurity:
    def test_clean_config_is_ok(self):
        assert check_prod_security(ROOT, _cfg()).status == "ok"

    def test_ok_detail_message(self):
        # ADR-032 : message OK exact « privilèges DB séparés et uploads bornés ».
        assert check_prod_security(ROOT, _cfg()).detail == (
            "privilèges DB séparés et uploads bornés"
        )

    def test_db_no_separation_warns(self, monkeypatch):
        # ADR-060 : check_prod_security lit les logins DB dans l'environnement.
        monkeypatch.setenv("DB_APP_LOGIN", "forge_admin")
        monkeypatch.setenv("DB_ADMIN_LOGIN", "forge_admin")
        r = check_prod_security(ROOT, _cfg(DB_APP_LOGIN="forge_admin"))
        assert r.status == "warn"
        assert "admin" in r.detail.lower()

    def test_unbounded_upload_warns(self):
        assert check_prod_security(ROOT, _cfg(UPLOAD_MAX_SIZE=0)).status == "warn"

    def test_non_numeric_upload_size_warns(self):
        assert check_prod_security(ROOT, _cfg(UPLOAD_MAX_SIZE="x")).status == "warn"

    def test_empty_extensions_warns(self, monkeypatch):
        # ADR-032 : l'avertissement se déclenche quand la variable d'environnement
        # est explicitement vidée (forge-mvc-files installé dans cet environnement).
        monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", "")
        assert check_prod_security(ROOT, _cfg()).status == "warn"

    def test_none_config_skips(self):
        assert check_prod_security(ROOT, None).status == "skip"


class TestIntegration:
    def test_registered_in_run_all(self):
        assert "check_prod_security" in inspect.getsource(doctor.run_all)
