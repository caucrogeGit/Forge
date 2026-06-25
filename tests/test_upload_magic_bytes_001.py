"""SEC-UPLOAD-MIME-MAGIC-001 — vérification pure des magic bytes d'upload (core).

Le `content_type` et l'extension étant fournis par le client, on vérifie le
contenu réel pour les types à signature connue (image/PDF).
"""
from __future__ import annotations

import pytest

from core.forms.upload_exceptions import UploadInvalidMimeTypeError
from core.forms.upload_validation import sniff_content_type, validate_magic_bytes

_PNG = b"\x89PNG\r\n\x1a\n" + b"....."
_JPEG = b"\xff\xd8\xff\xe0" + b"....."
_PDF = b"%PDF-1.7\n%...."
_GIF = b"GIF89a......"
_WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 "


@pytest.mark.parametrize(
    "content,expected",
    [
        (_PNG, "png"),
        (_JPEG, "jpeg"),
        (_PDF, "pdf"),
        (_GIF, "gif"),
        (_WEBP, "webp"),
        (b"<html>pas une image", None),
        (b"", None),
    ],
)
def test_sniff_content_type(content, expected):
    assert sniff_content_type(content) == expected


@pytest.mark.parametrize(
    "extension,content",
    [("png", _PNG), ("jpg", _JPEG), ("jpeg", _JPEG), ("pdf", _PDF), ("webp", _WEBP)],
)
def test_accepts_matching_content(extension, content):
    validate_magic_bytes(content, extension)  # ne lève pas


def test_rejects_html_named_png():
    with pytest.raises(UploadInvalidMimeTypeError):
        validate_magic_bytes(b"<html><script>alert(1)</script>", "png")


def test_rejects_png_content_named_jpg():
    with pytest.raises(UploadInvalidMimeTypeError):
        validate_magic_bytes(_PNG, "jpg")


@pytest.mark.parametrize("extension", ["txt", "csv", "bin", ""])
def test_skips_unknown_extensions(extension):
    # Pas de signature connue : non contraint (aucune exception).
    validate_magic_bytes(b"n'importe quel contenu", extension)
