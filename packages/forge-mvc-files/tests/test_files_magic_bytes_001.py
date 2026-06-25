"""SEC-UPLOAD-MIME-MAGIC-001 — save_upload refuse un contenu incohérent (files).

Vérifie de bout en bout que `save_upload` rejette un fichier dont le contenu ne
correspond pas à l'extension déclarée (le `content_type` client ne fait pas foi),
et ce AVANT toute écriture disque.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("forge_mvc_files")

from core.forms.upload_exceptions import UploadInvalidMimeTypeError  # noqa: E402
from forge_mvc_files.manager import save_upload  # noqa: E402


def test_save_upload_refuse_contenu_incoherent():
    bogus = SimpleNamespace(
        filename="evil.png",
        content_type="image/png",  # content_type menteur
        content=b"<html><script>alert(1)</script>",
    )
    with pytest.raises(UploadInvalidMimeTypeError):
        save_upload(bogus)


def test_save_upload_accepte_un_vrai_png(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    valid = SimpleNamespace(filename="ok.png", content_type="image/png", content=png)
    saved = save_upload(valid, category="images")
    assert saved.filename.endswith(".png")
