"""Garde-fou SEC-SESSION-FILE-PERMS-001.

Le backend de session fichier stocke l'état d'authentification, l'identité et le
jeton CSRF sur disque. Sur une machine multi-utilisateur, ces fichiers ne doivent
être lisibles que par le propriétaire. On vérifie que le dossier est en 0700 et
chaque fichier de session en 0600.

Les permissions POSIX n'ont pas d'équivalent sur Windows : le test y est ignoré.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from core.sessions.file_store import FileSessionStore

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="permissions POSIX uniquement (sans objet sur Windows)"
)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@posix_only
def test_le_dossier_de_sessions_est_0700(tmp_path: Path) -> None:
    sessions_dir = tmp_path / "sessions"
    FileSessionStore(sessions_dir=sessions_dir)
    assert _mode(sessions_dir) == 0o700


@posix_only
def test_le_dossier_preexistant_est_resserre_a_0700(tmp_path: Path) -> None:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sessions_dir.chmod(0o755)
    FileSessionStore(sessions_dir=sessions_dir)
    assert _mode(sessions_dir) == 0o700


@posix_only
def test_le_fichier_de_session_est_0600(tmp_path: Path) -> None:
    sessions_dir = tmp_path / "sessions"
    store = FileSessionStore(sessions_dir=sessions_dir)
    store.create({"user": "alice"})
    fichiers = list(sessions_dir.glob("*.json"))
    assert len(fichiers) == 1
    assert _mode(fichiers[0]) == 0o600


@posix_only
def test_le_fichier_reste_0600_apres_mise_a_jour(tmp_path: Path) -> None:
    sessions_dir = tmp_path / "sessions"
    store = FileSessionStore(sessions_dir=sessions_dir)
    session_id = store.create({"user": "alice"})
    store.set(session_id, {"authenticated": True})
    fichiers = list(sessions_dir.glob("*.json"))
    assert len(fichiers) == 1
    assert _mode(fichiers[0]) == 0o600
