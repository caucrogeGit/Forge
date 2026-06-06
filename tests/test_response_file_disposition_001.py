"""Tests RESPONSE-FILE-DISPOSITION-001 — Content-Disposition sans injection.

Response.file(download_name=...) interpolait le nom brut dans l'en-tete : un nom
contenant un guillemet ou un CR/LF permettait une injection d'en-tete. On assainit
le repli ASCII et on ajoute filename* (RFC 6266).
"""

from pathlib import Path

from core.http.response import Response


def _file(tmp_path) -> Path:
    p = tmp_path / "data.bin"
    p.write_bytes(b"hello")
    return p


def test_plain_name(tmp_path):
    r = Response.file(_file(tmp_path), download_name="rapport.pdf")
    cd = r.headers["Content-Disposition"]
    assert 'filename="rapport.pdf"' in cd
    assert "filename*=UTF-8''rapport.pdf" in cd


def test_quote_in_name_is_stripped_from_ascii_fallback(tmp_path):
    r = Response.file(_file(tmp_path), download_name='a"b.pdf')
    cd = r.headers["Content-Disposition"]
    # Le guillemet ne doit pas casser l'attribut fil="..." ni injecter.
    assert 'filename="ab.pdf"' in cd
    assert cd.count('"') == 2  # uniquement la paire entourant le fallback


def test_crlf_is_neutralised(tmp_path):
    r = Response.file(_file(tmp_path), download_name="evil\r\nSet-Cookie: x=1")
    cd = r.headers["Content-Disposition"]
    assert "\r" not in cd and "\n" not in cd


def test_unicode_uses_filename_star(tmp_path):
    r = Response.file(_file(tmp_path), download_name="résumé €.pdf")
    cd = r.headers["Content-Disposition"]
    assert "filename*=UTF-8''" in cd
    assert "%" in cd  # encodage percent des caracteres non-ASCII
