"""Tests MAIL-DECOUPLE-CORE-001 — la config mail est optionnelle dans le core.

Le mail est un opt-in (forge-mvc-mail, ADR-022). `core.app.app_factory` ne doit
plus exiger un bloc `MAIL_*` dans `config.py` : une application minimale qui n'en
a pas doit se construire sans `ImportError` sur le point d'entrée WSGI.
"""

import sys
import types

from core.app.app_factory import _forge_config_kwargs, _optional_mail_kwargs

_MAIL_KEYS = {
    "mail_host", "mail_port", "mail_username", "mail_password", "mail_from",
    "mail_use_tls", "mail_use_ssl", "mail_timeout", "mail_enabled",
    "mail_transport", "mail_log_dir", "mail_templates_dir", "mail_log_enabled",
}

# Symboles non-mail requis par _forge_config_kwargs(), pour construire un
# `config` minimal de substitution sans bloc MAIL_*.
_NON_MAIL_CONFIG = dict(
    APP_NAME="t", APP_ENV="test", VIEWS_DIR="mvc/views", SQL_DIR="mvc/models/sql",
    UPLOAD_ROOT="storage/uploads", UPLOAD_MAX_SIZE=1024,
    UPLOAD_ALLOWED_EXTENSIONS=frozenset({"png"}),
    UPLOAD_ALLOWED_MIME_TYPES=frozenset({"image/png"}),
    DB_APP_HOST="localhost", DB_APP_PORT=3306, DB_NAME="t",
    DB_APP_LOGIN="u", DB_APP_PWD="p", DB_POOL_SIZE=2,
    APP_TRUSTED_PROXIES=frozenset(),
)


def test_optional_mail_kwargs_present_with_real_config():
    """Le dogfood a un bloc MAIL_* : les 13 clés mail sont retournées."""
    kwargs = _optional_mail_kwargs()
    assert set(kwargs) == _MAIL_KEYS


def test_optional_mail_kwargs_degrades_without_mail_block(monkeypatch):
    """Sans bloc MAIL_* dans config, la lecture mail retourne {} (pas d'erreur)."""
    stub = types.ModuleType("config")  # config vide : aucun MAIL_*
    monkeypatch.setitem(sys.modules, "config", stub)
    assert _optional_mail_kwargs() == {}


def test_forge_config_kwargs_builds_without_mail_block(monkeypatch):
    """_forge_config_kwargs() se construit sans bloc MAIL_* et n'a aucune clé mail."""
    stub = types.ModuleType("config")
    for name, value in _NON_MAIL_CONFIG.items():
        setattr(stub, name, value)
    monkeypatch.setitem(sys.modules, "config", stub)

    kwargs = _forge_config_kwargs()

    assert not (_MAIL_KEYS & set(kwargs)), "aucune clé mail attendue sans bloc MAIL_*"
    assert kwargs["app_name"] == "t"
