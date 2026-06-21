"""Tests AUDIO-STORAGE-UUID-GUARD-001 — validation uuid sur le chemin d'écriture.

`resolve_playable_relpath` validait l'uuid en lecture, mais `store_original`
(écriture) ne le faisait pas : l'uuid apparaît dans l'arborescence
(`originals/<uuid>/`), donc un uuid non canonique fourni par l'appelant était un
vecteur de traversal à l'écriture. Symétrie lecture/écriture rétablie.
"""

import uuid as _uuid

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.storage import store_original


@pytest.mark.parametrize(
    "bad_uuid",
    ["../../etc/evil", "../escape", "not-a-uuid", "", "a/b", "..", "%2e%2e"],
)
def test_store_original_rejects_non_uuid(tmp_path, bad_uuid):
    with pytest.raises(ValueError):
        store_original(b"DATA", bad_uuid, ".mp3", storage_root=str(tmp_path))


def test_store_original_writes_nothing_on_traversal(tmp_path):
    with pytest.raises(ValueError):
        store_original(b"DATA", "../escape", ".mp3", storage_root=str(tmp_path))
    assert not list(tmp_path.rglob("*.mp3")), "aucun fichier ne doit être écrit"


def test_store_original_accepts_canonical_uuid(tmp_path):
    u = str(_uuid.uuid4())
    rel = store_original(b"DATA", u, ".mp3", storage_root=str(tmp_path))
    assert rel == f"originals/{u}/source.mp3"
    assert (tmp_path / rel).read_bytes() == b"DATA"
