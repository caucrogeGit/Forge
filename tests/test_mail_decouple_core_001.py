"""Tests MAIL-DECOUPLE-CORE-001 — le core ne connaît plus le mail (ADR-031).

`forge-mvc-mail` lit sa configuration depuis l'environnement. `core.forge` n'a
plus de slots `mail_*`, `core.forge.configure()` les refuse, et
`core.app.app_factory` ne thread plus aucune configuration mail.
"""

import sys
import types

import pytest

import core.forge as forge
from core.app.app_factory import _forge_config_kwargs

_MAIL_KEYS = {
    "mail_host", "mail_port", "mail_username", "mail_password", "mail_from",
    "mail_use_tls", "mail_use_ssl", "mail_timeout", "mail_enabled",
    "mail_transport", "mail_log_dir", "mail_templates_dir", "mail_log_enabled",
}

# Symboles non-mail requis par _forge_config_kwargs(), pour construire un
# `config` minimal de substitution sans aucun MAIL_*.
_NON_MAIL_CONFIG = dict(
    APP_NAME="t", APP_ENV="test", VIEWS_DIR="mvc/views", SQL_DIR="mvc/models/sql",
    UPLOAD_ROOT="storage/uploads", UPLOAD_MAX_SIZE=1024,
    UPLOAD_ALLOWED_EXTENSIONS=frozenset({"png"}),
    UPLOAD_ALLOWED_MIME_TYPES=frozenset({"image/png"}),
    DB_APP_HOST="localhost", DB_APP_PORT=3306, DB_NAME="t",
    DB_APP_LOGIN="u", DB_APP_PWD="p", DB_POOL_SIZE=2,
    APP_TRUSTED_PROXIES=frozenset(),
)


@pytest.mark.parametrize("key", sorted(_MAIL_KEYS))
def test_core_forge_has_no_mail_slot(key):
    """ADR-031 : aucun slot mail_* dans le registre du noyau."""
    with pytest.raises(KeyError):
        forge.get(key)


def test_configure_rejects_mail_keys():
    """configure() refuse toute clé mail : le core ne connaît plus le mail."""
    with pytest.raises(KeyError):
        forge.configure(mail_enabled=True)


def test_forge_config_kwargs_has_no_mail_key(monkeypatch):
    """_forge_config_kwargs() ne produit aucune clé mail."""
    stub = types.ModuleType("config")
    for name, value in _NON_MAIL_CONFIG.items():
        setattr(stub, name, value)
    monkeypatch.setitem(sys.modules, "config", stub)

    kwargs = _forge_config_kwargs()

    assert not (_MAIL_KEYS & set(kwargs)), "aucune clé mail attendue dans le core"
    assert kwargs["app_name"] == "t"


def test_skeleton_has_no_mail_plumbing():
    """Le squelette nu ne pré-câble plus le mail (env/config/app)."""
    from pathlib import Path
    root = Path(__file__).parent.parent / "forge_cli" / "skeleton" / "data"
    for rel in ("env/example", "config.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "MAIL_HOST" not in text and "MAIL_ENABLED" not in text, (
            f"{rel} ne doit plus contenir de variables MAIL_*"
        )
    app = (root / "app.py").read_text(encoding="utf-8")
    assert "mail_enabled" not in app and "MAIL_HOST" not in app, (
        "app.py ne doit plus passer de config mail à forge.configure"
    )
