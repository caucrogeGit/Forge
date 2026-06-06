"""Tests FILE-STORE-ATOMIC-WRITE-001 — écriture de session atomique.

_save écrit via un fichier temporaire puis os.replace : un crash en cours
d'écriture ne corrompt jamais le fichier existant, et aucun résidu .tmp ne doit
subsister après une écriture réussie.
"""

from core.sessions.file_store import FileSessionStore


def test_save_leaves_no_tmp_residue(tmp_path):
    store = FileSessionStore(sessions_dir=tmp_path / "sessions")
    sid = store.create()
    store.set(sid, {"k": "v"})
    store.set(sid, {"k": "v2"})

    sessions_dir = tmp_path / "sessions"
    assert not list(sessions_dir.glob("*.tmp")), "aucun fichier .tmp ne doit rester"
    assert store.get(sid)["k"] == "v2"


def test_save_roundtrip_after_replace(tmp_path):
    store = FileSessionStore(sessions_dir=tmp_path / "sessions")
    sid = store.create()
    store.replace(sid, {"a": 1, "expires_at": store.get(sid)["expires_at"]})
    assert store.get(sid)["a"] == 1
