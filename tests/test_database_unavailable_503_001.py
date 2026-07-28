"""MARIADB-POOL-QUEUE-001 : une surcharge répond 503, pas 500.

Quand toutes les connexions sont prises et qu'aucune ne se libère dans le
délai, la demande n'a rien d'invalide et l'application n'a aucun défaut : elle
est arrivée pendant une pointe.

Un `500` annoncerait une erreur du serveur et enverrait chercher un bug dans le
code, là où le remède est d'élargir `DB_POOL_SIZE` ou de raccourcir les
requêtes. `503 Service Unavailable` avec `Retry-After` dit la vérité : le
service est momentanément saturé, réessayez.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.app.application import Application
from core.database.errors import DatabaseError, DatabaseUnavailableError
from core.http.router import Router


@pytest.fixture(autouse=True)
def vues_du_squelette() -> Any:
    """Le rendu des pages d'erreur a besoin d'un dossier de vues réel."""
    from pathlib import Path

    import core.forge as forge
    from core.templating.manager import template_manager
    from integrations.jinja2.renderer import Jinja2Renderer

    vues = Path(__file__).resolve().parent / "fixtures" / "app" / "mvc" / "views"
    forge._cfg["views_dir"] = str(vues)  # pyright: ignore[reportPrivateUsage]
    template_manager.register(Jinja2Renderer(str(vues)))
    return vues


@pytest.fixture()
def app_qui_sature() -> Application:
    """Une application dont l'unique route bute sur un pool saturé."""

    def controleur(_request: Any) -> Any:
        raise DatabaseUnavailableError("Aucune connexion disponible après 5.0s d'attente.")

    router = Router()
    with router.group("", public=True) as public:
        public.add("GET", "/", controleur, name="accueil")
    return Application(router)


def test_une_surcharge_repond_503(app_qui_sature: Application, fake_request: Any) -> None:
    reponse = app_qui_sature.dispatch(fake_request(path="/"))

    assert reponse.status == 503


def test_la_reponse_invite_a_reessayer(app_qui_sature: Application, fake_request: Any) -> None:
    """`Retry-After` est ce qui distingue une saturation d'une panne."""
    reponse = app_qui_sature.dispatch(fake_request(path="/"))

    assert "Retry-After" in reponse.headers


def test_une_vraie_erreur_reste_un_500(fake_request: Any) -> None:
    """Le correctif ne doit pas transformer tout incident en surcharge."""

    def controleur(_request: Any) -> Any:
        raise RuntimeError("un vrai défaut du code")

    router = Router()
    with router.group("", public=True) as public:
        public.add("GET", "/", controleur, name="accueil")

    reponse = Application(router).dispatch(fake_request(path="/"))

    assert reponse.status == 500


def test_une_autre_erreur_bdd_reste_un_500(fake_request: Any) -> None:
    """Seule l'indisponibilité est une question de capacité.

    Un doublon ou une erreur de schéma relèvent de l'application, pas de la
    charge : les traiter en 503 inviterait à réessayer une requête qui
    échouera identiquement.
    """

    def controleur(_request: Any) -> Any:
        raise DatabaseError("contrainte violée")

    router = Router()
    with router.group("", public=True) as public:
        public.add("GET", "/", controleur, name="accueil")

    reponse = Application(router).dispatch(fake_request(path="/"))

    assert reponse.status == 500


def test_l_erreur_est_bien_une_erreur_de_base_de_donnees() -> None:
    """Une application peut l'attraper par la racine pour dégrader un écran."""
    assert issubclass(DatabaseUnavailableError, DatabaseError)


def test_le_squelette_livre_la_page_503() -> None:
    """Sans elle, le rendu du 503 échouerait et retomberait en 500."""
    from pathlib import Path

    racine = Path(__file__).resolve().parent.parent
    page = racine / "skeleton" / "data" / "mvc" / "views" / "errors" / "503.html"

    assert page.is_file()
    assert "503" in page.read_text(encoding="utf-8")


def test_le_503_tient_meme_sans_la_page(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Le cas de tous les projets existants : ils n'ont pas `errors/503.html`.

    Forge n'écrit jamais dans un projet (principe 9), donc une application
    créée avant cette page ne la recevra pas par une montée de version. Si le
    rendu échouait, la réponse retomberait en 500, soit exactement le message
    trompeur que ce 503 corrige.
    """
    import core.forge as forge
    from core.templating.manager import template_manager
    from integrations.jinja2.renderer import Jinja2Renderer

    vide = tmp_path / "views"
    vide.mkdir()
    monkeypatch.setitem(forge._cfg, "views_dir", str(vide))  # pyright: ignore[reportPrivateUsage]
    template_manager.register(Jinja2Renderer(str(vide)))

    def controleur(_request: Any) -> Any:
        raise DatabaseUnavailableError("saturé")

    router = Router()
    with router.group("", public=True) as public:
        public.add("GET", "/", controleur, name="accueil")

    from forge_mvc_testing.fake_request import FakeRequest

    reponse = Application(router).dispatch(FakeRequest(path="/"))

    assert reponse.status == 503
    assert reponse.headers["Retry-After"] == "2"
    assert b"eessayez" in reponse.body

