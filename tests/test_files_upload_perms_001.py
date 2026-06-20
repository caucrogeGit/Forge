"""Garde-fou FILES-UPLOAD-FILE-PERMS-001.

Un fichier uploadé doit avoir des permissions déterministes : lisible (donc
servable) mais jamais inscriptible par le groupe ou les autres, et indépendant
de l'umask du process. On vérifie l'invariant de sécurité sur POSIX.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_files")

from forge_mvc_files.storage import save_bytes

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="permissions POSIX uniquement (sans objet sur Windows)"
)


@posix_only
def test_fichier_uploade_non_inscriptible_par_autrui(tmp_path: Path) -> None:
    target = save_bytes(b"data", original_name="x.bin", category="documents", root=tmp_path)
    mode = stat.S_IMODE(target.stat().st_mode)
    # Aucun bit d'écriture pour le groupe ni les autres.
    assert mode & (stat.S_IWGRP | stat.S_IWOTH) == 0
    # Le propriétaire peut lire (média servable par l'application).
    assert mode & stat.S_IRUSR


@posix_only
def test_mode_ne_depasse_pas_0644(tmp_path: Path) -> None:
    target = save_bytes(b"data", original_name="y.bin", category="documents", root=tmp_path)
    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode & ~0o644 == 0
