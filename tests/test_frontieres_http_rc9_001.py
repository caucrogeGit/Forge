"""Trois défauts aux frontières entre composants, trouvés par une revue externe.

`CORE-HEADER-CRLF-COMPLETUDE-001`, `CORE-CSRF-TOKEN-NON-ASCII-001`,
`CORE-WSGI-PATH-DECODE-001`.

Les trois vivaient à la même sorte d'endroit : là où une couche passe la main à
une autre. Une suite de vingt-trois mille tests les laissait tous les trois
passer, parce qu'elle éprouvait chaque couche chez elle.

1. Le contrôle anti-injection d'en-têtes lisait le dictionnaire applicatif, et
   les deux serveurs ajoutaient ensuite `Content-Type` et les `Set-Cookie`.
2. La comparaison du jeton CSRF employait `hmac.compare_digest` sur des `str`,
   qui refuse le non-ASCII en levant `TypeError` : un refus devenait une panne.
3. L'adaptateur WSGI recollait `PATH_INFO` et `QUERY_STRING` pour les
   redécouper, alors que le serveur les avait déjà séparés et décodés.

Ce fichier éprouve la **sortie réelle** dans les trois cas, pas les fonctions
prises isolément : c'est ce qui manquait.
"""
from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from wsgiref.simple_server import WSGIRequestHandler, make_server

import pytest

from core.app.application import Application
from core.app.wsgi import _response_to_wsgi, create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.security.headers import HeaderInjectionError, assert_emitted_headers_are_safe
from core.security.middleware import CsrfMiddleware
from core.security.session import SESSION_COOKIE_NAME
from core.sessions.manager import get_session_store

CRLF = "\r\nX-Injected: yes"


def _emettre(response: Response) -> list[tuple[str, str]]:
    """Rend la liste d'en-têtes que le chemin WSGI passerait à `start_response`."""
    vus: dict[str, list[tuple[str, str]]] = {}

    def start_response(status: str, headers: list[tuple[str, str]], exc_info: object = None) -> None:
        vus["headers"] = headers

    _response_to_wsgi(response, start_response)
    return vus["headers"]


class TestInjectionDEntetes:
    """Aucune des voies d'émission n'échappe au contrôle."""

    def test_un_entete_applicatif_est_refuse(self) -> None:
        """Le témoin : cette voie était déjà couverte."""
        r = Response(status=200, body=b"x", content_type="text/plain")
        r.headers["X-Test"] = f"a{CRLF}"

        with pytest.raises(HeaderInjectionError):
            _emettre(r)

    def test_le_content_type_est_refuse(self) -> None:
        """Il était pris de `response.content_type`, après le contrôle."""
        r = Response(status=200, body=b"x", content_type=f"text/plain{CRLF}")

        with pytest.raises(HeaderInjectionError):
            _emettre(r)

    def test_un_cookie_est_refuse(self) -> None:
        """Les `Set-Cookie` étaient ajoutés après le contrôle, eux aussi."""
        r = Response(status=200, body=b"x", content_type="text/plain")
        r.add_cookie(f"a=b{CRLF}")

        with pytest.raises(HeaderInjectionError):
            _emettre(r)

    def test_une_reponse_saine_passe(self) -> None:
        """Un contrôle qui refuserait tout ne protégerait rien non plus."""
        r = Response(status=200, body=b"ok", content_type="text/html; charset=utf-8")
        r.add_cookie("s=1; Path=/; HttpOnly")

        emis = _emettre(r)

        assert ("Content-Type", "text/html; charset=utf-8") in emis
        assert ("Set-Cookie", "s=1; Path=/; HttpOnly") in emis

    @pytest.mark.parametrize("saut", ["\r", "\n", "\r\n"])
    def test_les_trois_formes_de_saut_sont_refusees(self, saut: str) -> None:
        """Un `\\r` seul suffit à découper la réponse pour certains clients."""
        with pytest.raises(HeaderInjectionError):
            assert_emitted_headers_are_safe([("X", f"a{saut}b")])

    def test_le_nom_est_controle_comme_la_valeur(self) -> None:
        with pytest.raises(HeaderInjectionError):
            assert_emitted_headers_are_safe([(f"X{CRLF}", "ok")])


class TestJetonCsrfNonAscii:
    """Une entrée invalide donne un refus, jamais une erreur serveur."""

    @staticmethod
    def _requete(jeton: str, session_id: str) -> object:
        class FauxRequest:
            body = {"csrf_token": [jeton]}
            headers = {"Cookie": f"{SESSION_COOKIE_NAME}={session_id}"}

            def get_cookie(self, nom: str, defaut: object = None) -> object:
                return session_id if nom == SESSION_COOKIE_NAME else defaut

        return FauxRequest()

    @pytest.fixture
    def session_id(self) -> str:
        store = get_session_store()
        sid = store.create()
        store.set(sid, {"csrf_token": "jeton-valide-ascii"})
        return sid

    @pytest.mark.parametrize(
        "jeton",
        ["mauvais", "é", "🙂", "\udcff", "é" * 5000, "", "  "],
        ids=["ascii-faux", "accent", "emoji", "surrogate", "tres-long", "vide", "espaces"],
    )
    def test_tout_jeton_invalide_donne_403(self, jeton: str, session_id: str) -> None:
        """`hmac.compare_digest` sur des `str` levait `TypeError` hors ASCII."""
        reponse = CsrfMiddleware().check(self._requete(jeton, session_id))

        assert reponse is not None, "un jeton invalide ne doit jamais être accepté"
        assert reponse.status == 403

    def test_le_jeton_correct_est_accepte(self, session_id: str) -> None:
        """Le remède ne doit pas refuser ce qui est valide."""
        assert CsrfMiddleware().check(self._requete("jeton-valide-ascii", session_id)) is None


class _Muet(WSGIRequestHandler):
    def log_message(self, *args: object) -> None:  # noqa: D102
        pass


@pytest.fixture(scope="module")
def serveur_wsgi():
    """Un vrai serveur WSGI : `PATH_INFO` doit venir d'un serveur, pas d'un dict.

    Fabriquer l'environ à la main referait l'erreur qu'on veut interdire, en
    posant un `PATH_INFO` déjà conforme à ce que le code attend.
    """
    def montre(request):
        return Response(
            status=200,
            content_type="application/json; charset=utf-8",
            body=json.dumps(
                {"nom": request.route_params.get("nom"), "params": request.params},
                ensure_ascii=False,
            ).encode("utf-8"),
        )

    router = Router()
    router.add("GET", "/files/{nom}", montre, public=True, csrf=False)
    router.add("GET", "/cherche", montre, public=True, csrf=False)
    application = Application(router, middlewares=[], api_routes_module=None)
    srv = make_server(
        "127.0.0.1", 0, create_wsgi_app(application, emit_prod_warnings=False), handler_class=_Muet
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown()


def _demander(port: int, chemin: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{chemin}", timeout=15) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


class TestAllerRetourDesUrl:
    """Ce qu'`url_for()` produit doit revenir intact au contrôleur."""

    @pytest.mark.parametrize(
        "valeur",
        ["a b", "a?b", "a#b", "café", "a&b", "a=b", "100%", "éé"],
        ids=["espace", "point-interrogation", "diese", "accent", "esperluette",
             "egal", "pourcent", "deux-accents"],
    )
    def test_un_parametre_de_chemin_revient_intact(self, valeur: str, serveur_wsgi: int) -> None:
        """`a?b` revenait `a`, et `café` revenait `cafÃ©`."""
        chemin = "/files/" + urllib.parse.quote(valeur, safe="")

        assert _demander(serveur_wsgi, chemin)["nom"] == valeur

    @pytest.mark.parametrize(
        "valeur",
        ["café", "a b", "a&b", "a?b", "100%"],
        ids=["accent", "espace", "esperluette", "point-interrogation", "pourcent"],
    )
    def test_un_parametre_de_requete_revient_intact(self, valeur: str, serveur_wsgi: int) -> None:
        """La chaîne de requête ne doit pas régresser en corrigeant le chemin."""
        chemin = "/cherche?" + urllib.parse.urlencode({"q": valeur})

        assert _demander(serveur_wsgi, chemin)["params"]["q"] == [valeur]

    def test_chemin_et_requete_ensemble(self, serveur_wsgi: int) -> None:
        """Le cas qui mélange les deux sources, là où le défaut vivait."""
        chemin = (
            "/files/" + urllib.parse.quote("a?b", safe="")
            + "?" + urllib.parse.urlencode({"q": "café"})
        )

        recu = _demander(serveur_wsgi, chemin)

        assert recu["nom"] == "a?b"
        assert recu["params"]["q"] == ["café"]
