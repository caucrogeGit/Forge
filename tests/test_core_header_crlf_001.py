"""CORE-HEADER-CRLF-001 : un saut de ligne dans un en-tête découpe la réponse.

Un `CR` ou un `LF` dans une valeur d'en-tête termine la ligne pour le client,
qui lit la suite comme un **nouvel en-tête**, voire comme le début du corps.
Une donnée utilisateur reprise dans un en-tête suffit : un nom de fichier en
`Content-Disposition`, une cible en `Location`, un identifiant en en-tête
applicatif. L'attaquant pose alors l'en-tête de son choix, `Set-Cookie`
compris, ou fait servir son propre corps de réponse.

Mesuré avant correctif, sur la pile WSGI réelle, les quatre charges sortaient
avec leur saut intact :

    "\\r\\nX-Injecte: 1"                    valeur émise avec le saut
    "\\nX-Injecte: 1"                      idem
    "\\rX-Injecte: 1"                      idem
    "ok\\r\\n\\r\\n<script>alert(1)</script>"   idem

Forge **refuse** la réponse plutôt que de retirer le caractère en silence.
Retirer modifierait une donnée applicative sans le dire, et la norme HTTP
n'admet aucun saut de ligne dans une valeur : il n'existe pas de cas légitime
à préserver.

Le contrôle vit dans `core.security.headers`, partagé par les deux chemins de
sortie, et s'exécute **avant** la première ligne émise : le serveur de
développement envoie ses en-têtes un par un, et refuser après coup serait trop
tard.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.security.headers import HeaderInjectionError, assert_headers_are_safe

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHARGES = [
    ("\r\nX-Injecte: 1", "CRLF"),
    ("\nX-Injecte: 1", "LF seul"),
    ("\rX-Injecte: 1", "CR seul"),
    ("ok\r\n\r\n<script>alert(1)</script>", "fin d'en-têtes puis corps"),
]


# ── La primitive ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("charge", "nom"), CHARGES, ids=[c[1] for c in CHARGES])
def test_une_valeur_avec_saut_de_ligne_est_refusee(charge: str, nom: str) -> None:
    with pytest.raises(HeaderInjectionError):
        assert_headers_are_safe({"X-Depuis-Utilisateur": f"valeur{charge}"})


def test_un_nom_d_en_tete_forge_est_refuse_aussi() -> None:
    """Une clé forgée ferait passer exactement la même chose que la valeur."""
    with pytest.raises(HeaderInjectionError):
        assert_headers_are_safe({"X-Normal\r\nX-Injecte": "v"})


def test_les_en_tetes_ordinaires_passent() -> None:
    """Le cas courant ne doit pas être gêné."""
    assert_headers_are_safe({
        "Location": "/accueil",
        "Content-Disposition": 'attachment; filename="rapport 2026.pdf"',
        "X-Trace": "a-b-c",
    })


def test_le_message_dit_ce_qui_est_refuse_et_pourquoi() -> None:
    with pytest.raises(HeaderInjectionError) as capture:
        assert_headers_are_safe({"X-Test": "a\r\nb"})

    message = str(capture.value)
    assert "saut de ligne" in message
    assert "X-Test" in message


# ── Le chemin WSGI ───────────────────────────────────────────────────────────

def _appeler_wsgi(valeur: str) -> "tuple[str | None, list[tuple[str, str]]]":
    routeur = Router()
    routeur.add("GET", "/x", lambda request: Response(
        200, "ok", headers={"X-Depuis-Utilisateur": valeur}), name="p", public=True)
    app = create_wsgi_app(Application(routeur))
    capture: "dict[str, object]" = {}

    def start_response(statut: str, entetes: "list[tuple[str, str]]",
                       exc_info: object = None) -> None:
        capture["statut"] = statut
        capture["entetes"] = entetes

    environ = {
        "REQUEST_METHOD": "GET", "PATH_INFO": "/x", "QUERY_STRING": "",
        "wsgi.input": BytesIO(b""), "CONTENT_LENGTH": "0",
        "SERVER_NAME": "t", "SERVER_PORT": "80", "wsgi.url_scheme": "http",
    }
    b"".join(app(environ, start_response))
    return capture.get("statut"), capture.get("entetes") or []  # type: ignore[return-value]


@pytest.mark.parametrize(("charge", "nom"), CHARGES, ids=[c[1] for c in CHARGES])
def test_wsgi_n_emet_jamais_de_saut_de_ligne(charge: str, nom: str) -> None:
    """Le cas mesuré : la valeur partait telle quelle vers le client."""
    try:
        _statut, entetes = _appeler_wsgi(f"valeur{charge}")
    except HeaderInjectionError:
        return  # refusé avant toute émission : c'est l'objectif

    for cle, valeur in entetes:
        assert "\r" not in valeur and "\n" not in valeur, (
            f"en-tête {cle} émis avec un saut de ligne"
        )
        assert "\r" not in cle and "\n" not in cle


def test_wsgi_sert_normalement_un_en_tete_sain() -> None:
    statut, entetes = _appeler_wsgi("valeur ordinaire")

    assert statut is not None and statut.startswith("200")
    assert ("X-Depuis-Utilisateur", "valeur ordinaire") in entetes


def test_le_controle_precede_start_response() -> None:
    """Refuser après la première ligne émise n'aurait aucun effet."""
    source = (PROJECT_ROOT / "core" / "app" / "wsgi.py").read_text(encoding="utf-8")
    position_controle = source.index("assert_headers_are_safe(")
    position_emission = source.index("start_response(_format_status")

    assert position_controle < position_emission


# ── Le jumeau : serveur de développement ─────────────────────────────────────

def test_le_serveur_de_dev_controle_aussi() -> None:
    """Les deux chemins de sortie doivent porter la même règle.

    Le serveur de développement est celui que le développeur exécute toute la
    journée ; l'oublier reviendrait à ne protéger que la production.
    """
    source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")

    assert "assert_headers_are_safe" in source
    position_controle = source.index("assert_headers_are_safe(")
    position_emission = source.index("self.send_response(response.status)")
    assert position_controle < position_emission, (
        "le contrôle doit précéder la première ligne émise"
    )


def test_le_serveur_de_dev_controle_aussi_les_cookies() -> None:
    """`add_cookie` accumule hors du dict d'en-têtes : il doit être couvert."""
    source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")
    bloc = source[source.index("_entetes_a_controler"):source.index("self.send_response")]

    assert "set_cookies" in bloc


# ── La règle vit à un seul endroit ───────────────────────────────────────────

def test_la_regle_n_est_pas_recopiee() -> None:
    """Une règle de sécurité recopiée finit incomplète (CRUD-CSV-ESCAPE-CORE-001)."""
    for chemin in ("core/app/wsgi.py", "skeleton/data/app.py"):
        source = (PROJECT_ROOT / chemin).read_text(encoding="utf-8")
        assert "from core.security.headers import" in source
        assert '"\\r" in' not in source, f"{chemin} réimplémente le contrôle"
