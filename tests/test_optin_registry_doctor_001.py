"""OPTIN-REGISTRY-DOCTOR-001 (ADR-061) — doctor signale registre vs .venv.

`forge doctor` compare les opt-ins (et le backend) inscrits dans optins/registry.py
aux paquets réellement installés, et avertit des divergences (déclaré mais absent).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


from cli.optins.registry_format import REGISTRY_TEMPLATE, add_optin_entry, set_backend
from cli.project.doctor import check_optin_registry


def _write_registry(tmp_path: Path, text: str) -> None:
    (tmp_path / "optins").mkdir(exist_ok=True)
    (tmp_path / "optins" / "registry.py").write_text(text, encoding="utf-8")


def test_registre_absent_skip(tmp_path):
    r = check_optin_registry(tmp_path)
    assert r.status == "skip"


def test_registre_vide_ok(tmp_path):
    _write_registry(tmp_path, REGISTRY_TEMPLATE)
    r = check_optin_registry(tmp_path)
    assert r.status == "ok"
    assert "aucun" in r.detail.lower()


def test_optin_inscrit_mais_absent_du_venv_warn(tmp_path, monkeypatch):
    text, _ = add_optin_entry(REGISTRY_TEMPLATE, "qrcode", "library")
    _write_registry(tmp_path, text)
    # Simule qrcode non installé.
    real = importlib.util.find_spec

    def fake(name, *a, **k):
        return None if name == "forge_mvc_qrcode" else real(name, *a, **k)

    monkeypatch.setattr(importlib.util, "find_spec", fake)
    r = check_optin_registry(tmp_path)
    assert r.status == "warn"
    assert "qrcode" in r.detail


def test_optin_inscrit_et_installe_ok(tmp_path, monkeypatch):
    text, _ = add_optin_entry(REGISTRY_TEMPLATE, "qrcode", "library")
    _write_registry(tmp_path, text)
    monkeypatch.setattr(importlib.util, "find_spec", lambda *a, **k: object())
    r = check_optin_registry(tmp_path)
    assert r.status == "ok"
    assert "1 inscrit" in r.detail


def test_backend_inscrit_mais_absent_warn(tmp_path, monkeypatch):
    text = set_backend(REGISTRY_TEMPLATE, "sqlite")
    _write_registry(tmp_path, text)
    monkeypatch.setattr(importlib.util, "find_spec", lambda *a, **k: None)
    r = check_optin_registry(tmp_path)
    assert r.status == "warn"
    assert "sqlite" in r.detail
