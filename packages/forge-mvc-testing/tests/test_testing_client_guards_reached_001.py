"""TESTING-CLIENT-GUARDS-REACHED-001 : les gardes sont vraiment traversées.

`ForgeTestClient` dit passer par le chemin de production, `create_wsgi_app`,
et sa docstring explique pourquoi : un client qui reconstruirait sa propre
boucle serait un **jumeau**, il passerait là où la production échoue, et les
deux dériveraient sans que rien ne le signale. Forge a déjà payé cette erreur
une fois, avec un serveur de développement qui répondait là où Gunicorn rendait
404.

Cette promesse était écrite et **jamais vérifiée**. Toutes les routes de
l'application d'essai du paquet se déclaraient `public=True, csrf=False` : pas
une seule ne passait par l'authentification ni par le contrôle anti-CSRF. Un
client qui aurait court-circuité les middlewares aurait donc laissé la suite
verte, ce qui est exactement le défaut que la docstring dit vouloir éviter.

Ces tests exercent les deux gardes dans les deux sens, et la boucle complète du
jeton, seule preuve que le cookie de session est bien reporté d'une requête à
la suivante.
"""
from __future__ import annotations

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.mvc.controller.base_controller import BaseController
from forge_mvc_testing import (
    ForgeTestClient,
    assert_authenticated,
    assert_not_authenticated,
    login_as,
    logout,
)


def _application() -> Application:
    """Une route par garde, plus la route qui rend le jeton."""
    routeur = Router()
    routeur.add("GET", "/libre", lambda r: Response.text("libre"),
                name="libre", public=True, csrf=False)
    routeur.add("GET", "/prive", lambda r: Response.text("secret"),
                name="prive", public=False, csrf=False)
    routeur.add("GET", "/jeton", lambda r: Response.text(BaseController.csrf_token(r)),
                name="jeton", public=True, csrf=False)
    routeur.add("POST", "/envoi", lambda r: Response.text("recu"),
                name="envoi", public=True, csrf=True)
    return Application(routeur)


@pytest.fixture
def client() -> ForgeTestClient:
    return ForgeTestClient(create_wsgi_app(_application(), emit_prod_warnings=False))


class TestGardeAuthentification:

    def test_une_route_publique_repond(self, client: ForgeTestClient) -> None:
        """Le témoin : sans lui, un client cassé ferait passer les autres tests."""
        assert client.get("/libre").status == 200

    def test_une_route_privee_est_refusee_sans_session(
        self, client: ForgeTestClient
    ) -> None:
        """Si le client court-circuitait le middleware, ce serait 200."""
        assert client.get("/prive").status == 302

    def test_login_as_ouvre_la_route_privee(self, client: ForgeTestClient) -> None:
        """La session posée doit être acceptée par la garde réelle, pas seulement écrite."""
        login_as(client, 42, roles=["admin"])

        assert client.get("/prive").status == 200

    def test_logout_la_referme(self, client: ForgeTestClient) -> None:
        login_as(client, 42)
        logout(client)

        assert client.get("/prive").status == 302


class TestGardeCsrf:

    def test_un_envoi_sans_jeton_est_refuse(self, client: ForgeTestClient) -> None:
        assert client.post("/envoi", data={"a": "1"}).status == 403

    def test_un_faux_jeton_est_refuse(self, client: ForgeTestClient) -> None:
        """Un contrôle qui accepterait n'importe quelle valeur ne garderait rien."""
        login_as(client, 42)

        assert client.post("/envoi", data={"csrf_token": "x" * 32}).status == 403

    def test_le_vrai_jeton_est_accepte(self, client: ForgeTestClient) -> None:
        """La boucle entière : connexion, lecture du jeton, envoi.

        Elle prouve aussi que le cookie de session est reporté d'une requête à
        la suivante : sans cela, le jeton lu appartiendrait à une autre session
        et serait refusé.
        """
        login_as(client, 42)
        jeton = client.get("/jeton").text.strip()

        assert len(jeton) == 32, "aucun jeton lisible : la session n'a pas suivi"
        assert client.post("/envoi", data={"csrf_token": jeton}).status == 200

    def test_le_jeton_passe_aussi_par_l_en_tete(self, client: ForgeTestClient) -> None:
        """La forme que retiennent les envois en JavaScript."""
        login_as(client, 42)
        jeton = client.get("/jeton").text.strip()

        reponse = client.post("/envoi", data={}, headers={"X-CSRF-Token": jeton})

        assert reponse.status == 200


class TestAssertionsNonVides:
    """Une assertion qui ne peut pas échouer affaiblit tout test qui l'emploie."""

    def test_assert_not_authenticated_echoue_apres_connexion(
        self, client: ForgeTestClient
    ) -> None:
        login_as(client, 42)

        with pytest.raises(AssertionError):
            assert_not_authenticated(client)

    def test_assert_authenticated_echoue_sans_connexion(
        self, client: ForgeTestClient
    ) -> None:
        with pytest.raises(AssertionError):
            assert_authenticated(client)

    def test_assert_authenticated_echoue_apres_deconnexion(
        self, client: ForgeTestClient
    ) -> None:
        login_as(client, 42)
        logout(client)

        with pytest.raises(AssertionError):
            assert_authenticated(client)
