"""Tests VIDEO-CLEANUP-001 : commande ``forge video:cleanup``.

dry-run par défaut, ``--apply`` pour exécuter. Aucune base réelle (repository
factice), fichiers réels sous ``tmp_path``. Couvre ``--failed``,
``--orphan-files`` et la défense anti-traversal.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.cli.cleanup import run_cleanup
from forge_mvc_video.config import VideoConfig


class FakeRepo:
    def __init__(self, failed=None, referenced=None):
        self._failed = failed or []
        self._referenced = set(referenced or set())
        self.deleted = []

    def list_by_status(self, status, limit=100):
        return list(self._failed)

    def all_relpaths(self):
        return set(self._referenced)

    def delete(self, video_id):
        self.deleted.append(video_id)


def _config(tmp_path):
    return VideoConfig(storage_root=str(tmp_path / "video"))


def _touch(tmp_path, relpath, data=b"x"):
    path = tmp_path / "video" / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


# ── Usage ────────────────────────────────────────────────────────────────────

def test_cleanup_sans_cible_retourne_usage(capsys):
    assert run_cleanup([], repository=FakeRepo(), config=None) == 2
    assert "Usage" in capsys.readouterr().out


# ── --failed ─────────────────────────────────────────────────────────────────

def _failed_row(rel):
    return {
        "id": 5,
        "original_path": rel,
        "mp4_path": None,
        "poster_path": None,
    }


def test_failed_dry_run_ne_supprime_rien(tmp_path, capsys):
    rel = "originals/2026/06/u1/source.mp4"
    f = _touch(tmp_path, rel)
    repo = FakeRepo(failed=[_failed_row(rel)])
    rc = run_cleanup(["--failed"], config=_config(tmp_path), repository=repo)
    assert rc == 0
    assert f.exists()            # dry-run : fichier conservé
    assert repo.deleted == []    # aucune ligne supprimée
    out = capsys.readouterr().out
    assert "DRY-RUN" in out and "--apply" in out


def test_failed_apply_supprime_fichiers_et_lignes(tmp_path, capsys):
    rel = "originals/2026/06/u1/source.mp4"
    f = _touch(tmp_path, rel)
    repo = FakeRepo(failed=[_failed_row(rel)])
    rc = run_cleanup(
        ["--failed", "--apply"], config=_config(tmp_path), repository=repo
    )
    assert rc == 0
    assert not f.exists()        # fichier supprimé
    assert repo.deleted == [5]   # ligne DB supprimée


# ── --orphan-files ───────────────────────────────────────────────────────────

def test_orphan_files_supprime_uniquement_les_non_references(tmp_path):
    ref = "originals/2026/06/known/source.mp4"
    orphan = "originals/2026/06/ghost/source.mp4"
    f_ref = _touch(tmp_path, ref)
    f_orphan = _touch(tmp_path, orphan)
    repo = FakeRepo(referenced={ref})
    rc = run_cleanup(
        ["--orphan-files", "--apply"], config=_config(tmp_path), repository=repo
    )
    assert rc == 0
    assert f_ref.exists()         # référencé : conservé
    assert not f_orphan.exists()  # orphelin : supprimé


def test_orphan_files_dry_run_conserve_tout(tmp_path):
    orphan = "originals/2026/06/ghost/source.mp4"
    f_orphan = _touch(tmp_path, orphan)
    repo = FakeRepo(referenced=set())
    rc = run_cleanup(
        ["--orphan-files"], config=_config(tmp_path), repository=repo
    )
    assert rc == 0
    assert f_orphan.exists()      # dry-run : rien supprimé


# ── Sécurité anti-traversal ──────────────────────────────────────────────────

def test_failed_ne_supprime_pas_hors_storage_root(tmp_path):
    # Un chemin DB malveillant ne doit pas faire sortir de storage_root.
    outside = tmp_path / "secret.txt"
    outside.write_text("ne pas toucher")
    repo = FakeRepo(failed=[_failed_row("../../secret.txt")])
    rc = run_cleanup(
        ["--failed", "--apply"], config=_config(tmp_path), repository=repo
    )
    assert rc == 0
    assert outside.exists()       # protégé par _safe_abspath
    assert repo.deleted == [5]    # la ligne DB est bien purgée, pas le fichier hors-racine
