"""CORE-WSGI-CSRF-POST-001 — la protection CSRF tient sur un vrai POST WSGI.

`core/forms` comptait quarante-six fonctions publiques, dont **une seule** était
atteinte par un appel WSGI réel. Or la validation d'un formulaire n'a de sens
qu'au bout de la chaîne : le corps doit d'abord être lu par l'adaptateur, décodé
selon son type de contenu, et seulement ensuite jugé.

Comme pour la protection d'accès, la propriété qui compte n'est pas « le
middleware rend un 403 » mais « **le contrôleur d'écriture ne s'exécute pas** ».
Un CSRF qui refuserait la requête après avoir laissé le contrôleur enregistrer
la modification protégerait exactement rien, et passerait tous les tests
unitaires du dépôt.

Le témoin est donc un effet de bord observable, pas un code de statut.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any
from urllib.parse import urlencode

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.sessions.access import SESSION_COOKIE_NAME
from core.sessions.manager import get_session_store

#: Effet de bord du contrôleur d'écriture : ce que la requête modifierait.
_registre: list[str] = []


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _post(path: str, champs: dict[str, str], *, cookie: str | None = None,
          entete_jeton: str | None = None) -> dict[str, Any]:
    corps = urlencode(champs).encode("utf-8")
    env: dict[str, Any] = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(corps)),
        "wsgi.input": BytesIO(corps),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }
    if cookie is not None:
        env["HTTP_COOKIE"] = cookie
    if entete_jeton is not None:
        env["HTTP_X_CSRF_TOKEN"] = entete_jeton
    return env


def controleur_ecriture(request: Any) -> Response:
    """Le contrôleur qui modifie. Il ne doit tourner qu'avec un jeton valide."""
    valeurs = request.body.get("titre") or [""]
    _registre.append(valeurs[0])
    return Response(200, "enregistré")


@pytest.fixture(autouse=True)
def registre_vide():
    _registre.clear()
    yield
    _registre.clear()


@pytest.fixture
def vues(tmp_path, monkeypatch):
    """Un dossier de vues réel avec un moteur enregistré.

    Reproduit ce que fait `build_application` au démarrage. Sans lui, le rendu
    de `errors/403.html` lève et l'on mesurerait un défaut de montage plutôt
    que le comportement du framework.
    """
    import core.forge as forge
    from core.templating.manager import template_manager
    from integrations.jinja2.renderer import Jinja2Renderer

    racine = tmp_path / "views"
    (racine / "errors").mkdir(parents=True)
    (racine / "errors" / "403.html").write_text(
        "<!doctype html><title>Refus</title><h1>Acces refuse</h1>", encoding="utf-8")

    ancien_dossier = forge._cfg.get("views_dir")
    ancien_moteur = template_manager._renderer  # pyright: ignore[reportPrivateUsage]
    forge._cfg["views_dir"] = str(racine)
    template_manager.register(Jinja2Renderer(str(racine)))
    yield racine
    forge._cfg["views_dir"] = ancien_dossier
    template_manager._renderer = ancien_moteur  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def wsgi_app(vues):
    router = Router()
    router.add("POST", "/articles", controleur_ecriture, public=True, csrf=True)
    router.add("POST", "/api/articles", controleur_ecriture, public=True, csrf=True, api=True)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


def _session_avec_jeton() -> tuple[str, str]:
    """Ouvre une session et rend son cookie et son jeton CSRF.

    Le jeton est engendré par le store à la création de la session : le lire
    plutôt que le fabriquer garantit que l'on exerce le jeton réel, pas une
    valeur que le middleware n'aurait aucune raison d'accepter.
    """
    store = get_session_store()
    session_id = store.create()
    donnees = store.get(session_id)
    assert donnees is not None
    jeton = donnees["csrf_token"]
    return f"{SESSION_COOKIE_NAME}={session_id}", jeton


# ── Contrôle de montage ──────────────────────────────────────────────────────


def test_le_jeton_de_session_est_bien_celui_du_store() -> None:
    """Sans ce contrôle, les tests de refus passeraient pour la mauvaise raison.

    Un cookie mal nommé rend la session invisible : il n'y a alors plus de
    jeton attendu, tout est refusé, et les tests de refus deviennent vides de
    sens. Le piège s'est déjà produit sur `__Host-session_id`
    (`CORE-WSGI-AUTH-GATE-001`).
    """
    cookie, jeton = _session_avec_jeton()

    assert cookie.startswith(SESSION_COOKIE_NAME + "=")
    assert jeton, "le store doit engendrer un jeton à la création de la session"


# ── Le refus ─────────────────────────────────────────────────────────────────


def test_un_post_sans_jeton_n_execute_pas_le_controleur(wsgi_app) -> None:
    """LE test : le refus doit précéder l'écriture, pas la suivre.

    Un CSRF qui rendrait un 403 après avoir laissé le contrôleur enregistrer
    protégerait exactement rien.
    """
    cookie, _jeton = _session_avec_jeton()
    start_response, capture = _capture()

    list(wsgi_app(_post("/articles", {"titre": "forgé"}, cookie=cookie), start_response))

    assert _registre == [], (
        "le contrôleur d'écriture s'est exécuté sans jeton : le 403 arrive trop tard"
    )
    assert capture["status"].startswith("403")


def test_un_post_sans_session_est_refuse(wsgi_app) -> None:
    """Sans session, il n'y a pas de jeton attendu : rien ne peut correspondre."""
    start_response, capture = _capture()

    list(wsgi_app(_post("/articles", {"titre": "forgé", "csrf_token": "invente"}),
                  start_response))

    assert _registre == []
    assert capture["status"].startswith("403")


def test_le_jeton_d_une_autre_session_est_refuse(wsgi_app) -> None:
    """Le cas réellement dangereux : un jeton valide, mais pas pour cette session.

    Un jeton engendré ailleurs est structurellement correct. Seule la
    comparaison avec celui de **la** session en cours le rejette.
    """
    cookie, _jeton = _session_avec_jeton()
    _autre_cookie, jeton_etranger = _session_avec_jeton()
    start_response, capture = _capture()

    list(wsgi_app(
        _post("/articles", {"titre": "forgé", "csrf_token": jeton_etranger}, cookie=cookie),
        start_response,
    ))

    assert _registre == [], "un jeton d'une autre session a été accepté"
    assert capture["status"].startswith("403")


# ── L'acceptation ────────────────────────────────────────────────────────────


def test_un_post_avec_le_bon_jeton_de_champ_passe(wsgi_app) -> None:
    """La contrepartie : tout refuser ferait passer les trois tests précédents.

    C'est aussi la seule preuve que le corps du formulaire est bien lu par
    l'adaptateur WSGI, décodé, et remis au contrôleur.
    """
    cookie, jeton = _session_avec_jeton()
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(
        _post("/articles", {"titre": "légitime", "csrf_token": jeton}, cookie=cookie),
        start_response,
    ))

    assert capture["status"].startswith("200"), (
        f"un jeton valide doit passer, obtenu {capture['status']}"
    )
    assert _registre == ["légitime"], (
        f"le corps du POST n'est pas parvenu au contrôleur : {_registre}"
    )
    assert b"enregistr" in corps


def test_un_post_avec_le_bon_jeton_d_entete_passe(wsgi_app) -> None:
    """La voie de l'en-tête, celle qu'emploie un appel JavaScript.

    Elle n'est pas une commodité : un client qui envoie du JSON n'a pas de
    champ de formulaire où loger le jeton.
    """
    cookie, jeton = _session_avec_jeton()
    start_response, capture = _capture()

    list(wsgi_app(
        _post("/articles", {"titre": "par en-tête"}, cookie=cookie, entete_jeton=jeton),
        start_response,
    ))

    assert capture["status"].startswith("200")
    assert _registre == ["par en-tête"]


# ── Le drapeau `api` sur un refus CSRF ───────────────────────────────────────


def test_un_refus_csrf_sur_une_api_ne_rend_pas_du_html(wsgi_app) -> None:
    """Un client d'API reçoit sinon une page d'erreur HTML qu'il ne sait pas lire.

    Il la journalise comme un corps de réponse, ou pire, la réaffiche.
    """
    cookie, _jeton = _session_avec_jeton()
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(
        _post("/api/articles", {"titre": "forgé"}, cookie=cookie), start_response))

    assert _registre == []
    assert capture["status"].startswith("403")
    entetes = {nom.lower(): valeur for nom, valeur in capture["headers"]}
    assert "application/json" in entetes.get("content-type", ""), (
        f"un refus CSRF sur une route d'API doit rester du JSON : {corps[:200]!r}"
    )


# ── Le socle de sécurité sur la réponse de refus ─────────────────────────────


def test_le_refus_porte_les_entetes_de_securite(wsgi_app) -> None:
    """Une réponse de refus reste une réponse : elle ne se dispense pas du socle."""
    cookie, _jeton = _session_avec_jeton()
    start_response, capture = _capture()

    list(wsgi_app(_post("/articles", {"titre": "forgé"}, cookie=cookie), start_response))

    entetes = {nom.lower() for nom, _ in capture["headers"]}

    assert "x-content-type-options" in entetes, (
        f"socle de sécurité absent de la réponse 403 : {sorted(entetes)}"
    )


# ── Quand le gabarit de refus est en défaut ──────────────────────────────────


@pytest.mark.parametrize(
    ("cas", "gabarit"),
    [
        ("syntaxe Jinja invalide", "{% if %}<h1>Refus</h1>"),
        ("filtre inconnu", "{{ 'x' | filtre_qui_nexiste_pas }}"),
        ("variable absente", "{{ absente.methode() }}"),
    ],
)
def test_un_gabarit_403_casse_ne_transforme_pas_le_refus_en_panne(
    wsgi_app, vues, cas: str, gabarit: str
) -> None:
    """Un refus doit rester un refus, quoi qu'il arrive au gabarit.

    `errors/403.html` **appartient à l'utilisateur** : le squelette le livre et
    Forge n'y réécrit jamais (principe 4). Un projet peut donc le casser.

    Le refus devenait alors un `500`, ce qui dit le contraire de la vérité. Un
    `403` annonce une requête invalide, qu'il ne sert à rien de rejouer ; un
    `500` annonce une panne du serveur et invite à réessayer. L'exploitant, de
    son côté, voit une vague de pannes là où son application refuse
    correctement des requêtes forgées.

    Le contrôleur d'écriture ne s'exécute pas davantage : c'est la propriété de
    sécurité, et elle tenait déjà. C'est le **code rendu** qui mentait.
    """
    (vues / "errors" / "403.html").write_text(gabarit, encoding="utf-8")
    cookie, _jeton = _session_avec_jeton()
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_post("/articles", {"titre": "forgé"}, cookie=cookie),
                              start_response))

    assert _registre == [], "la propriété de sécurité doit tenir dans tous les cas"
    assert capture["status"].startswith("403"), (
        f"gabarit 403 en défaut ({cas}) : le refus est devenu « {capture['status']} », "
        "ce qui invite le client à rejouer sa requête et noie l'exploitant sous "
        "de fausses pannes"
    )
    assert corps, "un corps vide laisse le navigateur sans rien à afficher"
