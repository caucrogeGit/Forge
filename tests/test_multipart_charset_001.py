"""CORE-MULTIPART-CHARSET-001 : un jeu de caractères inconnu ne fait plus tomber la requête.

Le décodage d'un champ multipart utilise le jeu de caractères **déclaré par le
client**. `bytes.decode()` lève deux exceptions distinctes : `UnicodeDecodeError`
pour des octets invalides, et `LookupError` pour un encodage inconnu. Seule la
première était interceptée.

N'importe quel client pouvait donc provoquer une **500** en envoyant
`Content-Type: text/plain; charset=charset-bidon` dans une part de formulaire.
Entrée non fiable, aucune authentification requise.

Le champ indécodable vaut la chaîne vide, comme toute valeur illisible. Un jeu
de caractères légitime mais non UTF-8 doit continuer de se décoder : le
correctif ne doit pas se transformer en repli systématique.
"""
from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from core.http.request import Request

BOUNDARY = "----forge-multipart"
CONTENT_TYPE = f"multipart/form-data; boundary={BOUNDARY}"


def _part(charset: str | None, payload: bytes, *, name: str = "titre") -> bytes:
    lines = [f"--{BOUNDARY}", f'Content-Disposition: form-data; name="{name}"']
    if charset is not None:
        lines.append(f"Content-Type: text/plain; charset={charset}")
    head = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")
    return head + payload + f"\r\n--{BOUNDARY}--\r\n".encode("utf-8")


def _parse(raw: bytes) -> dict[str, list[str]]:
    body, _files = Request._parse_multipart(CONTENT_TYPE, raw)
    return body


# ── Le défaut corrigé ────────────────────────────────────────────────────────

def test_un_jeu_de_caracteres_inconnu_ne_leve_plus() -> None:
    assert _parse(_part("charset-bidon", b"bonjour")) == {"titre": [""]}


@pytest.mark.parametrize(
    "charset",
    ["charset-bidon", "utf-42", "", "x" * 200, "utf-8;evil", "../../etc/passwd"],
)
def test_aucun_jeu_de_caracteres_hostile_ne_fait_tomber_l_analyse(charset: str) -> None:
    """Le nom vient de la requête : aucune valeur ne doit propager d'exception."""
    body = _parse(_part(charset, b"bonjour"))
    assert set(body) == {"titre"}


def test_des_octets_invalides_restent_traites_comme_avant() -> None:
    assert _parse(_part("utf-8", b"\xff\xfe\x00")) == {"titre": [""]}


# ── Ce qui doit continuer de marcher ─────────────────────────────────────────

def test_le_cas_nominal_est_intact() -> None:
    assert _parse(_part("utf-8", "bonjour".encode("utf-8"))) == {"titre": ["bonjour"]}


def test_un_jeu_de_caracteres_legitime_non_utf8_se_decode_toujours() -> None:
    """Le correctif ne doit pas devenir un repli systématique sur la chaîne vide."""
    assert _parse(_part("latin-1", "café".encode("latin-1"))) == {"titre": ["café"]}


def test_sans_jeu_de_caracteres_declare_l_utf8_reste_le_defaut() -> None:
    assert _parse(_part(None, "café".encode("utf-8"))) == {"titre": ["café"]}


# ── Bout en bout : une requête HTTP complète ─────────────────────────────────

class _FakeHeaders:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = {key.lower(): value for key, value in data.items()}

    def get(self, name: str, default: str = "") -> str:
        return self._data.get(name.lower(), default)


def test_une_requete_complete_ne_leve_pas_sur_un_charset_inconnu() -> None:
    """Le chemin réel : c'est là que l'exception remontait en 500."""
    raw = _part("charset-bidon", b"bonjour")
    handler = SimpleNamespace(
        command="POST",
        path="/articles/create",
        headers=_FakeHeaders({
            "Content-Type": CONTENT_TYPE,
            "Content-Length": str(len(raw)),
        }),
        rfile=io.BytesIO(raw),
        client_address=("127.0.0.1", 12345),
    )

    request = Request(handler)

    assert request.form("titre") == ""
