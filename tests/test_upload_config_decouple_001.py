"""Tests UPLOAD-CONFIG-DECOUPLE-001 — périmètre de la config upload (ADR-032).

Seul `upload_max_size` reste un réglage du noyau (il borne le corps multipart
dans core/http/request.py). Les quatre autres clés quittent `core.forge` et le
squelette nu, vers les opt-ins files / images qui les lisent depuis l'env.
"""

import re
import sys
import types

import pytest

import core.forge as forge
from core.app.app_factory import _forge_config_kwargs

_MOVED_KEYS = {
    "upload_root",
    "upload_allowed_extensions",
    "upload_allowed_mime_types",
    "upload_max_image_pixels",
}

_SKELETON = __import__("pathlib").Path(__file__).parent.parent / "skeleton" / "data"


@pytest.mark.parametrize("key", sorted(_MOVED_KEYS))
def test_core_forge_has_no_moved_upload_slot(key):
    """ADR-032 : les 4 clés déplacées ne sont plus dans le registre du noyau."""
    with pytest.raises(KeyError):
        forge.get(key)


def test_upload_max_size_reste_dans_le_core():
    """upload_max_size reste un réglage du noyau (borne le corps multipart)."""
    assert isinstance(forge.get("upload_max_size"), int)


@pytest.mark.parametrize("key", sorted(_MOVED_KEYS))
def test_configure_rejette_les_cles_deplacees(key):
    with pytest.raises(KeyError):
        forge.configure(**{key: "x"})


def test_forge_config_kwargs_garde_max_size_sans_les_autres(monkeypatch):
    """_forge_config_kwargs() ne thread que upload_max_size, plus les 4 autres."""
    stub = types.ModuleType("config")
    for name, value in dict(
        APP_NAME="t", APP_ENV="test", VIEWS_DIR="mvc/views", SQL_DIR="mvc/models/sql",
        UPLOAD_MAX_SIZE=1024,
        DB_APP_HOST="localhost", DB_APP_PORT=3306, DB_NAME="t",
        DB_APP_LOGIN="u", DB_APP_PWD="p", DB_POOL_SIZE=2,
        APP_TRUSTED_PROXIES=frozenset(),
    ).items():
        setattr(stub, name, value)
    monkeypatch.setitem(sys.modules, "config", stub)

    kwargs = _forge_config_kwargs()

    assert kwargs["upload_max_size"] == 1024
    assert not (_MOVED_KEYS & set(kwargs)), "aucune des 4 clés déplacées ne doit être threadée"


def test_squelette_nu_sans_config_upload_deplacee():
    """env/example, config.py, app.py du squelette : UPLOAD_MAX_SIZE conservé,
    aucune AFFECTATION des clés déplacées (les commentaires explicatifs sont tolérés)."""
    for rel in ("env/example", "config.py", "app.py"):
        text = (_SKELETON / rel).read_text(encoding="utf-8")
        # Affectations majuscules (env var / module config.py) et kwargs minuscules (app.py).
        assert not re.search(r"(?mi)^\s*UPLOAD_ROOT\s*=", text), rel
        assert not re.search(r"(?mi)^\s*UPLOAD_ALLOWED_EXTENSIONS\s*=", text), rel
        assert not re.search(r"(?mi)^\s*UPLOAD_ALLOWED_MIME_TYPES\s*=", text), rel
        assert not re.search(r"(?m)^\s*upload_root\s*=", text), rel
        assert not re.search(r"(?m)^\s*upload_allowed_(extensions|mime_types)\s*=", text), rel
        assert "UPLOAD_MAX_SIZE" in text, f"{rel} doit conserver UPLOAD_MAX_SIZE"
