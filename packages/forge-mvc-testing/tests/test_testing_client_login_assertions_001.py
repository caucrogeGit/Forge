"""Les quatre tickets `testing` du cycle rc8.

`TESTING-CLIENT-001`, `TESTING-LOGIN-AS-001`, `TESTING-FIXTURES-ALIGN-001` et
`TESTING-ASSERTIONS-001`.

`FakeRequest` permet d'appeler un contrôleur directement. C'est utile et
insuffisant : rien n'y passe par le routeur, ni par les middlewares, ni par la
construction d'une `Request` depuis un environnement WSGI. Un test qui appelle
`Controller.show(fake_request)` ne prouve donc rien du CSRF, de
l'authentification, ni même de l'existence de la route.

Le client de test passe par le **vrai** callable WSGI, celui que Gunicorn
appelle. Un client qui reconstruirait sa propre boucle serait un jumeau, et
Forge a déjà payé cette erreur une fois.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.sessions.access import SESSION_COOKIE_NAME
from core.sessions.manager import get_session_store
from forge_mvc_testing import (
    ClientResponse,
    ForgeTestClient,
    FixturesUnavailable,
    ClientError,
    assert_authenticated,
    assert_no_session,
    assert_not_authenticated,
    assert_session_key,
    assert_session_rotated,
    assert_token_consumed,
    assert_token_valid,
    load_fixture_scenario,
    login_as,
    logout,
    session_of,
)


def _application() -> Application:
    router = Router()
    router.add("GET", "/salut", lambda r: Response.text("bonjour"),
               name="salut", public=True, csrf=False)
    router.add("GET", "/json", lambda r: Response.json({"ok": True}),
               name="j", public=True, csrf=False, api=True)
    router.add("GET", "/vers",
               lambda r: Response(302, b"", "text/plain", headers={"Location": "/salut"}),
               name="v", public=True, csrf=False)
    router.add("POST", "/echo", lambda r: Response.text(str(r.form("nom"))),
               name="e", public=True, csrf=False)
    router.add("GET", "/entetes",
               lambda r: Response.text(str(r.header("X-Essai"))),
               name="h", public=True, csrf=False)
    return Application(router)


@pytest.fixture
def client() -> ForgeTestClient:
    return ForgeTestClient(create_wsgi_app(_application(), emit_prod_warnings=False))


# ------------------------------------------------------- TESTING-CLIENT


class TestCheminReel:

    def test_il_passe_par_le_callable_wsgi(self, client: ForgeTestClient) -> None:
        """Ce n'est pas un détail d'élégance.

        Un client qui reconstruirait sa propre boucle passerait là où la
        production échoue, et les deux dériveraient sans que rien ne le
        signale.
        """
        assert client.get("/salut").text == "bonjour"

    def test_le_routeur_est_traverse(self, client: ForgeTestClient) -> None:
        """Une route absente rend 404, ce qu'un appel direct au contrôleur ne
        pourrait pas montrer."""
        assert client.get("/route/inexistante").status == 404

    def test_la_methode_compte(self, client: ForgeTestClient) -> None:
        assert client.post("/salut").status in (404, 405)

    def test_une_application_non_wsgi_est_signalee(self) -> None:
        def _muette(environ: Any, start_response: Any) -> list[bytes]:
            return [b""]

        with pytest.raises(ClientError, match="start_response"):
            ForgeTestClient(_muette).get("/")  # type: ignore[arg-type]


class TestRequete:

    def test_le_corps_de_formulaire_arrive(self, client: ForgeTestClient) -> None:
        assert client.post("/echo", data={"nom": "Durand"}).text == "Durand"

    def test_le_corps_json_arrive(self, client: ForgeTestClient) -> None:
        assert client.post("/echo", json={"nom": "X"}).status == 200

    def test_les_deux_corps_ensemble_sont_refuses(self, client: ForgeTestClient) -> None:
        """Laisser l'un gagner en silence produirait un test qui vérifie autre
        chose que ce qu'il croit."""
        with pytest.raises(ClientError, match="qu'un corps"):
            client.post("/echo", data={"a": "1"}, json={"a": 1})

    def test_les_en_tetes_sont_transmis(self, client: ForgeTestClient) -> None:
        assert client.get("/entetes", headers={"X-Essai": "valeur"}).text == "valeur"

    def test_la_chaine_de_requete_du_chemin_est_gardee(
        self, client: ForgeTestClient
    ) -> None:
        assert client.get("/salut?a=1").status == 200

    def test_query_s_ajoute_au_chemin(self, client: ForgeTestClient) -> None:
        assert client.get("/salut?a=1", query={"b": "2"}).status == 200


class TestReponse:

    def test_le_code_est_numerique(self, client: ForgeTestClient) -> None:
        assert client.get("/salut").status == 200

    def test_le_json_est_decode(self, client: ForgeTestClient) -> None:
        assert client.get("/json").json() == {"ok": True}

    def test_un_corps_non_json_le_dit_avec_son_debut(
        self, client: ForgeTestClient
    ) -> None:
        """Une page d'erreur HTML rendue là où du JSON était attendu se
        diagnostique en la lisant."""
        with pytest.raises(ClientError, match="Début du corps"):
            client.get("/salut").json()

    def test_les_en_tetes_sont_insensibles_a_la_casse(
        self, client: ForgeTestClient
    ) -> None:
        reponse = client.get("/salut")

        assert reponse.header("content-type") == reponse.header("Content-Type")

    def test_un_corps_mal_encode_ne_leve_pas(self) -> None:
        """Un test qui échoue doit montrer la page, et une exception de
        décodage masquerait le vrai motif."""
        reponse = ClientResponse("200 OK", [], b"\xff\xfe invalide")

        assert "invalide" in reponse.text


class TestRedirection:

    def test_elle_n_est_pas_suivie_par_defaut(self, client: ForgeTestClient) -> None:
        reponse = client.get("/vers")

        assert reponse.status == 302
        assert reponse.location == "/salut"

    def test_elle_se_suit_sur_demande(self, client: ForgeTestClient) -> None:
        assert client.get("/vers", follow_redirects=True).text == "bonjour"

    def test_une_seule_redirection_est_suivie(self, client: ForgeTestClient) -> None:
        """Une boucle de redirections est un défaut à voir, pas à absorber :
        la suivre indéfiniment ferait tourner le test sans fin."""
        router = Router()
        router.add("GET", "/boucle",
                   lambda r: Response(302, b"", "text/plain",
                                      headers={"Location": "/boucle"}),
                   name="b", public=True, csrf=False)
        boucleur = ForgeTestClient(
            create_wsgi_app(Application(router), emit_prod_warnings=False)
        )

        assert boucleur.get("/boucle", follow_redirects=True).status == 302


class TestCookies:

    def test_ils_sont_gardes_entre_deux_requetes(self, client: ForgeTestClient) -> None:
        """Un scénario réaliste enchaîne connexion, formulaire et envoi."""
        client.cookies["essai"] = "valeur"

        assert client.cookies["essai"] == "valeur"

    def test_un_cookie_efface_est_retire(self) -> None:
        """Garder le cookie ferait passer un test de déconnexion qui ne prouve
        rien."""
        router = Router()
        router.add(
            "GET", "/deconnexion",
            lambda r: Response(200, b"", "text/plain",
                               headers={"Set-Cookie": "jeton=; Max-Age=0; Path=/"}),
            name="d", public=True, csrf=False,
        )
        c = ForgeTestClient(create_wsgi_app(Application(router), emit_prod_warnings=False))
        c.cookies["jeton"] = "abc"

        c.get("/deconnexion")

        assert "jeton" not in c.cookies

    def test_on_peut_repartir_a_zero(self, client: ForgeTestClient) -> None:
        client.cookies["a"] = "1"
        client.clear_cookies()

        assert client.cookies == {}


# ----------------------------------------------------- TESTING-LOGIN-AS


class TestAuthentificationDeTest:

    def test_elle_passe_par_le_vrai_magasin(self, client: ForgeTestClient) -> None:
        """Fabriquer le cookie soi même produirait un jumeau : le test
        passerait avec une session que la production aurait refusée."""
        identifiant = login_as(client, 42)

        assert get_session_store().get(identifiant) is not None

    def test_le_cookie_est_pose(self, client: ForgeTestClient) -> None:
        identifiant = login_as(client, 42)

        assert client.cookies[SESSION_COOKIE_NAME] == identifiant

    def test_la_session_est_authentifiee(self, client: ForgeTestClient) -> None:
        login_as(client, 42)

        assert_authenticated(client)

    def test_l_utilisateur_est_rangé_en_session(self, client: ForgeTestClient) -> None:
        login_as(client, 42, roles=["admin"])
        donnees = session_of(client) or {}

        assert donnees["user"]["id"] == 42
        assert donnees["user"]["roles"] == ["admin"]

    def test_la_cle_canonique_du_pont_est_posee(self, client: ForgeTestClient) -> None:
        """L'omettre laisserait une session « authentifiée » que le cœur ne
        reconnaît pas, et le test échouerait pour une raison illisible."""
        from core.sessions.keys import SESSION_KEY_AUTH_USER_ID

        login_as(client, 42)

        assert (session_of(client) or {})[SESSION_KEY_AUTH_USER_ID] == 42

    def test_des_donnees_libres_s_ajoutent(self, client: ForgeTestClient) -> None:
        login_as(client, 42, email="a@b.fr")

        assert (session_of(client) or {})["user"]["email"] == "a@b.fr"

    def test_la_deconnexion_detruit_la_session(self, client: ForgeTestClient) -> None:
        """Oublier le cookie sans détruire la session laisserait un test de
        déconnexion passer alors que la session reste utilisable."""
        identifiant = login_as(client, 42)

        logout(client)

        assert get_session_store().get(identifiant) is None
        assert SESSION_COOKIE_NAME not in client.cookies

    def test_sans_session_le_contenu_est_absent(self, client: ForgeTestClient) -> None:
        assert session_of(client) is None

    def test_aucun_utilisateur_n_est_cree_en_base(self, client: ForgeTestClient) -> None:
        """Un test de contrôle d'accès vérifie ce que le middleware fait d'une
        session, pas ce que le dépôt contient."""
        import ast

        import forge_mvc_testing.auth_helper as module

        arbre = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        importes = {
            (n.module or "") for n in ast.walk(arbre) if isinstance(n, ast.ImportFrom)
        }

        assert not any(m.startswith("core.database") for m in importes)


# --------------------------------------------------- TESTING-ASSERTIONS


class TestAssertionsDeSession:

    def test_sans_cookie_le_message_le_dit(self, client: ForgeTestClient) -> None:
        with pytest.raises(AssertionError, match="aucun cookie"):
            assert_authenticated(client)

    def test_un_cookie_orphelin_le_dit_aussi(self, client: ForgeTestClient) -> None:
        """Trois échecs possibles qu'un `assert` unique confondrait."""
        client.cookies[SESSION_COOKIE_NAME] = "inexistante"

        with pytest.raises(AssertionError, match="ne correspond à aucune session"):
            assert_authenticated(client)

    def test_une_session_anonyme_le_dit_aussi(self, client: ForgeTestClient) -> None:
        magasin = get_session_store()
        client.cookies[SESSION_COOKIE_NAME] = magasin.create()

        with pytest.raises(AssertionError, match="n'est pas authentifiée"):
            assert_authenticated(client)

    def test_non_authentifie_tolere_une_session_anonyme(
        self, client: ForgeTestClient
    ) -> None:
        """Un visiteur en a une dès qu'il reçoit un jeton CSRF."""
        client.cookies[SESSION_COOKIE_NAME] = get_session_store().create()

        assert_not_authenticated(client)

    def test_non_authentifie_echoue_sur_une_session_authentifiee(
        self, client: ForgeTestClient
    ) -> None:
        login_as(client, 42)

        with pytest.raises(AssertionError, match="est authentifié"):
            assert_not_authenticated(client)

    def test_aucune_session_est_plus_strict(self, client: ForgeTestClient) -> None:
        client.cookies[SESSION_COOKIE_NAME] = get_session_store().create()

        with pytest.raises(AssertionError, match="porte encore la session"):
            assert_no_session(client)

    def test_une_cle_de_session_se_verifie(self, client: ForgeTestClient) -> None:
        login_as(client, 42)

        assert assert_session_key(client, "authenticated") is True

    def test_une_cle_absente_liste_celles_presentes(
        self, client: ForgeTestClient
    ) -> None:
        login_as(client, 42)

        with pytest.raises(AssertionError, match="Clés présentes"):
            assert_session_key(client, "jamais_posee")

    def test_un_ecart_montre_les_deux_valeurs(self, client: ForgeTestClient) -> None:
        """« attendu 3, trouvé '3' » se corrige, « faux » ne se corrige pas."""
        login_as(client, 42)

        with pytest.raises(AssertionError, match="attendu.*trouvé"):
            assert_session_key(client, "authenticated", expected="oui")


class TestRotationDeSession:

    def test_elle_exige_un_identifiant_different(
        self, client: ForgeTestClient
    ) -> None:
        avant = login_as(client, 1)

        with pytest.raises(AssertionError, match="n'a pas changé"):
            assert_session_rotated(avant, client)

    def test_elle_exige_que_l_ancienne_soit_morte(
        self, client: ForgeTestClient
    ) -> None:
        """Changer l'identifiant sans détruire l'ancien ne protège de rien."""
        magasin = get_session_store()
        avant = magasin.create()
        client.cookies[SESSION_COOKIE_NAME] = magasin.create()

        with pytest.raises(AssertionError, match="toujours vivante"):
            assert_session_rotated(avant, client)

    def test_une_vraie_rotation_passe(self, client: ForgeTestClient) -> None:
        magasin = get_session_store()
        avant = magasin.create()
        magasin.delete(avant)
        apres = login_as(client, 1)

        assert assert_session_rotated(avant, client) == apres

    def test_une_deconnexion_n_est_pas_une_rotation(
        self, client: ForgeTestClient
    ) -> None:
        avant = login_as(client, 1)
        logout(client)

        with pytest.raises(AssertionError, match="déconnexion"):
            assert_session_rotated(avant, client)


class _MagasinJetons:
    def __init__(self) -> None:
        self.consommes: set[str] = set()

    def is_used(self, token: str) -> bool:
        return token in self.consommes


class TestAssertionsDeJeton:

    def test_un_jeton_neuf_est_valide(self) -> None:
        assert_token_valid(_MagasinJetons(), "abcdef123456")

    def test_un_jeton_consomme_n_est_plus_valide(self) -> None:
        magasin = _MagasinJetons()
        magasin.consommes.add("abcdef123456")

        with pytest.raises(AssertionError, match="déjà consommé"):
            assert_token_valid(magasin, "abcdef123456")

    def test_un_jeton_non_consomme_est_signale(self) -> None:
        """Un jeton à usage unique qui reste utilisable après emploi est une
        faille silencieuse."""
        with pytest.raises(AssertionError, match="rejouable"):
            assert_token_consumed(_MagasinJetons(), "abcdef123456")

    def test_un_jeton_consomme_passe(self) -> None:
        magasin = _MagasinJetons()
        magasin.consommes.add("abcdef123456")

        assert_token_consumed(magasin, "abcdef123456")

    def test_un_magasin_sans_methode_connue_le_dit(self) -> None:
        with pytest.raises(AssertionError, match="aucune méthode"):
            assert_token_consumed(object(), "abc")


# ---------------------------------------------- TESTING-FIXTURES-ALIGN


class TestChargementDeFixtures:

    def test_il_reutilise_le_code_du_paquet_fixtures(self, tmp_path: Path) -> None:
        """Pas une seconde implémentation : les mêmes fichiers, le même ordre.

        En recalculer un second ici le ferait dériver.
        """
        pytest.importorskip("forge_mvc_fixtures")

        (tmp_path / "mvc" / "fixtures").mkdir(parents=True)
        (tmp_path / "mvc" / "fixtures" / "01_roles.sql").write_text(
            "INSERT INTO roles VALUES (1);", encoding="utf-8"
        )
        jouees: list[str] = []

        joues = load_fixture_scenario(tmp_path, jouees.append)

        assert joues == ["01_roles.sql"]
        assert jouees == ["INSERT INTO roles VALUES (1)"]

    def test_un_scenario_se_choisit(self, tmp_path: Path) -> None:
        pytest.importorskip("forge_mvc_fixtures")

        base = tmp_path / "mvc" / "fixtures"
        (base / "demo").mkdir(parents=True)
        (base / "demo" / "10_a.sql").write_text("INSERT INTO a VALUES (1);", encoding="utf-8")

        joues = load_fixture_scenario(tmp_path, lambda _sql: None, scenario="demo")

        assert joues == ["10_a.sql"]

    def test_le_paquet_absent_est_dit(self, monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path) -> None:
        import importlib

        def _absent(nom: str) -> Any:
            raise ImportError(nom)

        monkeypatch.setattr(importlib, "import_module", _absent)

        with pytest.raises(FixturesUnavailable, match="pip install"):
            load_fixture_scenario(tmp_path, lambda _sql: None)

    def test_la_fixture_pytest_est_exposee(self, fixtures_loader: Any) -> None:
        """Le plugin l'expose à toute la suite, y compris aux paquets opt-in."""
        assert callable(fixtures_loader)

    def test_la_fabrique_de_client_est_exposee(self, make_client: Any) -> None:
        client = make_client(_application())

        assert client.get("/salut").status == 200
