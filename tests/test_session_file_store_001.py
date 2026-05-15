"""Tests pour SESSION-FILE-STORE-001 — Backend session fichier."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path):
    from core.sessions.file_store import FileSessionStore
    return FileSessionStore(sessions_dir=tmp_path / "sessions")


@pytest.fixture
def store_ttl0(tmp_path):
    from core.sessions.file_store import FileSessionStore
    return FileSessionStore(sessions_dir=tmp_path / "sessions", ttl=0)


@pytest.fixture
def sessions_dir(tmp_path):
    return tmp_path / "sessions"


# ── Importabilité ─────────────────────────────────────────────────────────────


def test_file_session_store_importable():
    from core.sessions.file_store import FileSessionStore
    assert callable(FileSessionStore)


def test_file_store_importable_from_core_sessions():
    from core.sessions import FileSessionStore
    assert callable(FileSessionStore)


def test_file_store_implements_protocol(tmp_path):
    from core.sessions import SessionStore
    from core.sessions.file_store import FileSessionStore
    store = FileSessionStore(sessions_dir=tmp_path / "sessions")
    assert isinstance(store, SessionStore)


# ── Création ──────────────────────────────────────────────────────────────────


def test_file_store_create_returns_64_hex(store):
    sid = store.create()
    assert isinstance(sid, str)
    assert len(sid) == 64
    assert all(c in "0123456789abcdef" for c in sid)


def test_file_store_create_writes_file(store, tmp_path):
    sid = store.create()
    assert (tmp_path / "sessions" / f"{sid}.json").exists()


def test_file_store_create_file_is_json(store, tmp_path):
    sid = store.create()
    raw = json.loads((tmp_path / "sessions" / f"{sid}.json").read_text(encoding="utf-8"))
    assert isinstance(raw, dict)


def test_file_store_create_standard_structure(store):
    sid = store.create()
    data = store.get(sid)
    assert data is not None
    assert data["authenticated"] is False
    assert data["user"] is None
    assert "csrf_token" in data
    assert "expires_at" in data


def test_file_store_creates_dir_if_absent(tmp_path):
    from core.sessions.file_store import FileSessionStore
    new_dir = tmp_path / "deep" / "nested" / "sessions"
    store = FileSessionStore(sessions_dir=new_dir)
    assert new_dir.exists()
    store.create()


# ── Lecture ───────────────────────────────────────────────────────────────────


def test_file_store_get_returns_data(store):
    sid = store.create()
    assert store.get(sid) is not None


def test_file_store_get_unknown_returns_none(store):
    assert store.get("a" * 64) is None


def test_file_store_get_invalid_id_returns_none(store):
    assert store.get("invalid") is None


def test_file_store_get_empty_string_returns_none(store):
    assert store.get("") is None


# ── Modification ──────────────────────────────────────────────────────────────


def test_file_store_set_updates_data(store):
    sid = store.create()
    store.set(sid, {"custom_key": "custom_value"})
    data = store.get(sid)
    assert data is not None
    assert data["custom_key"] == "custom_value"
    assert data["authenticated"] is False


def test_file_store_set_unknown_is_noop(store):
    store.set("a" * 64, {"x": 1})


def test_file_store_set_invalid_id_is_noop(store):
    store.set("../evil", {"x": 1})


# ── Suppression ───────────────────────────────────────────────────────────────


def test_file_store_delete_removes_session(store, tmp_path):
    sid = store.create()
    store.delete(sid)
    assert store.get(sid) is None
    assert not (tmp_path / "sessions" / f"{sid}.json").exists()


def test_file_store_delete_unknown_is_noop(store):
    store.delete("a" * 64)


def test_file_store_delete_invalid_id_is_noop(store):
    store.delete("../evil")


# ── Régénération ──────────────────────────────────────────────────────────────


def test_file_store_regenerate_returns_new_id(store):
    sid = store.create()
    nouveau = store.regenerate(sid)
    assert nouveau != sid
    assert len(nouveau) == 64


def test_file_store_regenerate_preserves_data(store):
    sid = store.create()
    store.set(sid, {"user_key": "user_val"})
    nouveau = store.regenerate(sid)
    data = store.get(nouveau)
    assert data is not None
    assert data["user_key"] == "user_val"


def test_file_store_regenerate_old_id_gone(store):
    sid = store.create()
    store.regenerate(sid)
    assert store.get(sid) is None


# ── Expiration ────────────────────────────────────────────────────────────────


def test_file_store_expired_returns_none(store_ttl0):
    sid = store_ttl0.create()
    time.sleep(0.01)
    assert store_ttl0.get(sid) is None


def test_file_store_expired_file_deleted(store_ttl0, tmp_path):
    sid = store_ttl0.create()
    time.sleep(0.01)
    store_ttl0.get(sid)
    assert not (tmp_path / "sessions" / f"{sid}.json").exists()


# ── Nettoyage ─────────────────────────────────────────────────────────────────


def test_file_store_cleanup_expired_removes_files(tmp_path):
    from core.sessions.file_store import FileSessionStore
    store = FileSessionStore(sessions_dir=tmp_path / "sessions", ttl=0)
    store.create()
    store.create()
    time.sleep(0.01)
    count = store.cleanup_expired()
    assert count == 2
    assert list((tmp_path / "sessions").glob("*.json")) == []


def test_file_store_cleanup_keeps_valid_sessions(tmp_path):
    from core.sessions.file_store import FileSessionStore
    short = FileSessionStore(sessions_dir=tmp_path / "sessions", ttl=0)
    long_ = FileSessionStore(sessions_dir=tmp_path / "sessions", ttl=3600)
    short.create()
    sid_valid = long_.create()
    time.sleep(0.01)
    short.cleanup_expired()
    assert long_.get(sid_valid) is not None


def test_file_store_cleanup_returns_count(tmp_path):
    from core.sessions.file_store import FileSessionStore
    store = FileSessionStore(sessions_dir=tmp_path / "sessions", ttl=0)
    for _ in range(5):
        store.create()
    time.sleep(0.01)
    assert store.cleanup_expired() == 5


def test_file_store_cleanup_empty_dir_returns_zero(store):
    assert store.cleanup_expired() == 0


# ── Sessions corrompues ───────────────────────────────────────────────────────


def test_file_store_corrupted_json_returns_none(store, tmp_path):
    sid = store.create()
    (tmp_path / "sessions" / f"{sid}.json").write_text("not json", encoding="utf-8")
    assert store.get(sid) is None


def test_file_store_corrupted_json_no_exception(store, tmp_path):
    sid = store.create()
    (tmp_path / "sessions" / f"{sid}.json").write_text("{bad: json}", encoding="utf-8")
    try:
        store.get(sid)
    except Exception as exc:
        pytest.fail(f"get() a levé une exception sur fichier corrompu : {exc}")


def test_file_store_wrong_type_returns_none(store, tmp_path):
    sid = store.create()
    (tmp_path / "sessions" / f"{sid}.json").write_text('["liste", "pas", "dict"]', encoding="utf-8")
    assert store.get(sid) is None


# ── Protection path traversal ─────────────────────────────────────────────────


def test_path_traversal_get_rejected(store):
    assert store.get("../../../etc/passwd" + "a" * 45) is None
    assert store.get("../../secret") is None
    assert store.get("/" + "a" * 63) is None


def test_path_traversal_delete_no_effect(store, tmp_path):
    (tmp_path / "outside.json").write_text("{}", encoding="utf-8")
    store.delete("../outside" + "a" * 54)
    assert (tmp_path / "outside.json").exists()


def test_non_hex_id_rejected(store):
    assert store.get("G" * 64) is None
    assert store.get("A" * 64) is None
    assert store.get("0" * 63 + "!") is None
    assert store.get("-" * 64) is None


def test_set_path_traversal_no_effect(store, tmp_path):
    (tmp_path / "victim.json").write_text('{"secret": true}', encoding="utf-8")
    store.set("../victim" + "a" * 55, {"inject": True})
    raw = json.loads((tmp_path / "victim.json").read_text(encoding="utf-8"))
    assert "inject" not in raw


def test_files_stay_within_sessions_dir(store, tmp_path):
    for bad in ["../evil", "../../etc/passwd", "/absolute/path"]:
        store.delete(bad)
        store.set(bad, {"x": 1})
        store.get(bad)
    assert not (tmp_path / "evil.json").exists()


# ── Sérialiseurs dangereux absents ───────────────────────────────────────────

_BANNED = ["pic" + "kle", "mar" + "shal", "ev" + "al(", "ex" + "ec("]


def test_banned_serializers_absent_from_file_store():
    source = (ROOT / "core" / "sessions" / "file_store.py").read_text(encoding="utf-8")
    for word in _BANNED:
        assert word not in source, f"mot interdit dans file_store.py : {word}"


def test_banned_serializers_absent_from_this_test():
    source = Path(__file__).read_text(encoding="utf-8")
    for word in _BANNED:
        assert word not in source, f"mot interdit dans le fichier de test : {word}"


# ── Format JSON ───────────────────────────────────────────────────────────────


def test_file_format_is_valid_json(store, tmp_path):
    sid = store.create()
    path = tmp_path / "sessions" / f"{sid}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    assert "expires_at" in raw


def test_file_contains_expire_a(store, tmp_path):
    sid = store.create()
    raw = json.loads((tmp_path / "sessions" / f"{sid}.json").read_text(encoding="utf-8"))
    assert isinstance(raw["expires_at"], float)


# ── Backend par défaut inchangé ───────────────────────────────────────────────


def test_default_store_is_still_memory_store():
    from core.sessions import get_session_store, MemorySessionStore
    assert isinstance(get_session_store(), MemorySessionStore)


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_reference_session_file_store_001():
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "SESSION-FILE-STORE-001" in content
