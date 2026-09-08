"""`TESTING-CLIENT-FIDELITE-WSGI-001` — le client doit être fidèle, pas commode.

Trois écarts avec un vrai serveur WSGI, trouvés par une revue externe et
reproduits :

1. `base_url="https://…"` ne changeait rien : `wsgi.url_scheme` restait `http`,
   et l'hôte restait `testserver:80`. Un test de cookie `Secure` semblait donc
   passer sur une connexion claire.
2. `PATH_INFO` gardait son percent-encoding, là où PEP 3333 impose un chemin
   **décodé**, représenté en latin-1.
3. `data={"ids": ["1", "2"]}` devenait un champ unique valant `"['1', '2']"`,
   au lieu de deux valeurs `ids`.

Le second point est le plus instructif : il **masquait** le défaut de décodage
d'URL du cœur (`CORE-WSGI-PATH-DECODE-001`). Un client qui n'encode pas comme
un serveur ne peut pas révéler qu'un serveur décode mal. Un outil de mesure
faux ne rend pas les tests inutiles, il les rend rassurants.

L'étalon de ce fichier est donc un **vrai serveur WSGI**, jamais une valeur
attendue écrite à la main : cette valeur serait à son tour une opinion sur ce
qu'un serveur fait.
"""
from __future__ import annotations

import threading
import urllib.parse
import urllib.request
from wsgiref.simple_server import WSGIRequestHandler, make_server

import pytest

pytest.importorskip("forge_mvc_testing")

from forge_mvc_testing.client import ForgeTestClient  # noqa: E402

CLES_COMPAREES = ("PATH_INFO", "QUERY_STRING", "wsgi.url_scheme")


class _Muet(WSGIRequestHandler):
    def log_message(self, *args: object) -> None:  # noqa: D102
        pass


@pytest.fixture
def temoin():
    """Une application WSGI qui relève ce qu'elle reçoit, et le serveur qui la sert."""
    vu: dict[str, object] = {}

    def application(environ, start_response):
        taille = int(environ.get("CONTENT_LENGTH") or 0)
        vu["environ"] = dict(environ)
        vu["corps"] = environ["wsgi.input"].read(taille).decode("utf-8") if taille else ""
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    serveur = make_server("127.0.0.1", 0, application, handler_class=_Muet)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    yield application, vu, serveur.server_address[1]
    serveur.shutdown()


class TestFideliteAuServeurReel:
    """Ce que le client fabrique doit être ce qu'un serveur produirait."""

    @pytest.mark.parametrize(
        "chemin",
        ["/simple", "/caf%C3%A9", "/files/a%3Fb", "/files/a%23b", "/a%20b", "/100%25"],
        ids=["simple", "accent", "point-interrogation", "diese", "espace", "pourcent"],
    )
    def test_le_chemin_est_celui_du_serveur(self, chemin: str, temoin) -> None:
        """`PATH_INFO` gardait son percent-encoding, contre PEP 3333."""
        application, vu, port = temoin

        urllib.request.urlopen(f"http://127.0.0.1:{port}{chemin}", timeout=15).read()
        attendu = vu["environ"]["PATH_INFO"]

        ForgeTestClient(application, base_url=f"http://127.0.0.1:{port}").get(chemin)
        obtenu = vu["environ"]["PATH_INFO"]

        assert obtenu == attendu, (
            f"le client fabrique {obtenu!r} là où un serveur produit {attendu!r}"
        )

    def test_la_chaine_de_requete_est_celle_du_serveur(self, temoin) -> None:
        application, vu, port = temoin
        chemin = "/cherche?" + urllib.parse.urlencode({"q": "café", "n": "1"})

        urllib.request.urlopen(f"http://127.0.0.1:{port}{chemin}", timeout=15).read()
        attendu = {c: vu["environ"][c] for c in CLES_COMPAREES}

        ForgeTestClient(application, base_url=f"http://127.0.0.1:{port}").get(chemin)

        assert {c: vu["environ"][c] for c in CLES_COMPAREES} == attendu


class TestOrigine:
    """`base_url` doit décider du schéma, de l'hôte et du port."""

    @pytest.mark.parametrize(
        ("base", "schema", "hote", "port"),
        [
            ("https://example.test", "https", "example.test", "443"),
            ("http://example.test", "http", "example.test", "80"),
            ("https://example.test:8443", "https", "example.test", "8443"),
            ("http://testserver", "http", "testserver", "80"),
        ],
    )
    def test_l_origine_suit_l_url_de_base(
        self, base: str, schema: str, hote: str, port: str, temoin
    ) -> None:
        """Le schéma restait `http`, donc un cookie `Secure` semblait posé en clair."""
        application, vu, _ = temoin

        ForgeTestClient(application, base_url=base).get("/x")
        environ = vu["environ"]

        assert environ["wsgi.url_scheme"] == schema
        assert environ["SERVER_NAME"] == hote
        assert environ["SERVER_PORT"] == port

    def test_l_hote_porte_le_port_quand_il_n_est_pas_par_defaut(self, temoin) -> None:
        application, vu, _ = temoin

        ForgeTestClient(application, base_url="https://example.test:8443").get("/x")

        assert vu["environ"]["HTTP_HOST"] == "example.test:8443"


class TestFormulaireMultivalue:
    """Une liste vaut plusieurs champs de même nom, comme dans un navigateur."""

    def test_une_liste_donne_plusieurs_valeurs(self, temoin) -> None:
        """Elle donnait un champ unique valant la représentation Python de la liste."""
        application, vu, _ = temoin

        ForgeTestClient(application).post("/x", data={"ids": ["1", "2"]})

        assert urllib.parse.parse_qs(vu["corps"])["ids"] == ["1", "2"]

    def test_un_tuple_aussi(self, temoin) -> None:
        application, vu, _ = temoin

        ForgeTestClient(application).post("/x", data={"ids": ("a", "b")})

        assert urllib.parse.parse_qs(vu["corps"])["ids"] == ["a", "b"]

    def test_none_reste_une_valeur_vide(self, temoin) -> None:
        """Le contrat d'avant : `None` vaut la chaîne vide, pas la disparition."""
        application, vu, _ = temoin

        ForgeTestClient(application).post("/x", data={"n": None, "x": 3})

        recu = urllib.parse.parse_qs(vu["corps"], keep_blank_values=True)
        assert recu["n"] == [""]
        assert recu["x"] == ["3"]

    def test_le_corps_est_celui_qu_un_navigateur_enverrait(self, temoin) -> None:
        application, vu, _ = temoin

        ForgeTestClient(application).post("/x", data={"ids": ["1", "2"], "q": "café"})

        assert "ids=1&ids=2" in vu["corps"]
        assert "q=caf%C3%A9" in vu["corps"]
