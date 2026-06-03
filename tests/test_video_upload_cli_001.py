"""Tests VIDEO-UPLOAD-CLI-001 : commande ``forge video:upload``.

Aucune base réelle (``DbAdapter`` factice), stockage dans ``tmp_path``, aucun
ffmpeg/ffprobe lancé. Exercice de la chaîne complète parse → lecture fichier →
ingest → stockage → insertion DB.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.cli.upload import _parse_title, run_upload
from forge_mvc_video.config import VideoConfig
from forge_mvc_video.storage.repository import VideoRepository


class FakeDb:
    def __init__(self):
        self.calls = []
        self.next_id = 42

    def insert(self, sql, params):
        self.calls.append(("insert", sql, params))
        return self.next_id

    def execute(self, sql, params):
        self.calls.append(("execute", sql, params))

    def fetch_one(self, sql, params):
        return None

    def fetch_all(self, sql, params):
        return []


def _config(tmp_path, *, max_upload_mb=10):
    return VideoConfig(storage_root=str(tmp_path / "video"), max_upload_mb=max_upload_mb)


def _write(tmp_path, name="clip.mp4", data=b"\x00\x01\x02\x03"):
    path = tmp_path / name
    path.write_bytes(data)
    return str(path)


# ── Parsing --title ──────────────────────────────────────────────────────────

def test_parse_title_separate():
    title, rest = _parse_title(["clip.mp4", "--title", "Ma vidéo"])
    assert title == "Ma vidéo"
    assert rest == ["clip.mp4"]


def test_parse_title_equals():
    title, rest = _parse_title(["--title=Bonjour", "clip.mp4"])
    assert title == "Bonjour"
    assert rest == ["clip.mp4"]


def test_parse_title_absent():
    title, rest = _parse_title(["clip.mp4"])
    assert title is None
    assert rest == ["clip.mp4"]


# ── Usage / erreurs ──────────────────────────────────────────────────────────

def test_upload_sans_fichier_retourne_usage(capsys):
    assert run_upload([]) == 2
    assert "Usage" in capsys.readouterr().out


def test_upload_fichier_introuvable(tmp_path, capsys):
    rc = run_upload(
        [str(tmp_path / "absent.mp4")],
        config=_config(tmp_path),
        repository=VideoRepository(FakeDb()),
    )
    assert rc == 2
    assert "introuvable" in capsys.readouterr().out


def test_upload_extension_refusee(tmp_path, capsys):
    path = _write(tmp_path, name="doc.txt")
    rc = run_upload(
        [path], config=_config(tmp_path), repository=VideoRepository(FakeDb())
    )
    assert rc == 1
    assert "refusé" in capsys.readouterr().out


def test_upload_fichier_vide_refuse(tmp_path, capsys):
    path = _write(tmp_path, name="vide.mp4", data=b"")
    rc = run_upload(
        [path], config=_config(tmp_path), repository=VideoRepository(FakeDb())
    )
    assert rc == 1
    assert "refusé" in capsys.readouterr().out


# ── Succès : chaîne complète ─────────────────────────────────────────────────

def test_upload_succes_insere_et_stocke(tmp_path, capsys):
    fake = FakeDb()
    path = _write(tmp_path, name="film.mp4", data=b"\x00" * 2048)
    rc = run_upload(
        [path, "--title", "Mon film"],
        config=_config(tmp_path),
        repository=VideoRepository(fake),
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "id=42" in out and "uuid=" in out

    # Le titre nettoyé est bien passé à l'INSERT.
    kind, _sql, params = fake.calls[-1]
    assert kind == "insert"
    assert "Mon film" in params

    # Le fichier source a été écrit sous storage_root/originals/...
    originals = tmp_path / "video" / "originals"
    written = list(originals.rglob("source.mp4"))
    assert len(written) == 1
    assert written[0].read_bytes() == b"\x00" * 2048


def test_upload_sans_titre_passe_none(tmp_path):
    fake = FakeDb()
    path = _write(tmp_path, name="film.mp4", data=b"\x00" * 1024)
    rc = run_upload(
        [path], config=_config(tmp_path), repository=VideoRepository(fake)
    )
    assert rc == 0
    _kind, _sql, params = fake.calls[-1]
    assert None in params  # title None inséré
