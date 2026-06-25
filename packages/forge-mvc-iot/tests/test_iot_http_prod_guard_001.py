"""SEC-IOT-TOKEN-PROD-001 — l'API IoT ouverte (sans token) est refusée en prod.

Sécuriser par défaut : `register_iot_routes` lève en `APP_ENV=prod` si aucun token
n'est configuré ; le mode ouvert reste autorisé hors production, et avec token.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_iot")

from core.http.router import Router  # noqa: E402
from forge_mvc_iot import http  # noqa: E402
from forge_mvc_iot.config import load_iot_config  # noqa: E402


def _env(app_env: str):
    return lambda key: app_env if key == "app_env" else None


def test_refuse_open_api_in_prod(monkeypatch):
    monkeypatch.setattr(http, "_forge_get", _env("prod"))
    with pytest.raises(RuntimeError, match="production"):
        http.register_iot_routes(Router(), config=load_iot_config(env={}))


def test_allow_open_api_in_dev(monkeypatch):
    monkeypatch.setattr(http, "_forge_get", _env("dev"))
    # Mode ouvert préservé hors production : aucune exception.
    http.register_iot_routes(Router(), config=load_iot_config(env={}))


def test_allow_token_in_prod(monkeypatch):
    monkeypatch.setattr(http, "_forge_get", _env("prod"))
    # Avec token configuré, l'enregistrement en production est autorisé.
    http.register_iot_routes(
        Router(),
        config=load_iot_config(env={"FORGE_IOT_API_TOKEN": "secret-token"}),
    )
