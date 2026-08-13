"""CORE-WSGI-ERROR-PATH-001 — le chemin d'erreur tient sous WSGI réel.

Le sous-système `core/errors` n'était atteint par **aucun** appel WSGI réel :
douze fonctions publiques, toutes vérifiées en appel direct. C'est le pire
endroit pour cette lacune, puisque ce code ne tourne que lorsque tout le reste
a déjà échoué.

## Ce qui se joue précisément

`Application.dispatch` rattrape l'exception d'un contrôleur, puis rend
`errors/500.html`. Ce gabarit **appartient à l'utilisateur** : le squelette le
livre, et Forge n'y réécrit jamais (principe 4). Un projet peut donc parfaitement
le casser, en y glissant une erreur de syntaxe Jinja ou une variable absente.

Or `core.http.helpers.html` ne rattrape que `TemplateNotFoundError`. Toute
autre erreur de rendu ressort de `dispatch`, traverse le callable WSGI qui ne
la rattrape pas, et c'est le serveur qui répond. Sous Gunicorn, l'utilisateur
reçoit la page du serveur, sans les en-têtes de sécurité de Forge, et la
**cause première est perdue** : ce que l'exploitant voit est l'erreur du
gabarit d'erreur, pas celle qui a réellement échoué.

Cette famille de divergences a déjà mordu deux fois, `/health` répondant 404
derrière Gunicorn et `request.data` levant sur tout le chemin de production.
Un test qui passe par un adaptateur fait main ne dit rien du serveur réel.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.router import Router
from integrations.jinja2.renderer import Jinja2Renderer
from core.templating.manager import template_manager

#: Ce que la réponse ne doit jamais contenir en production. Le nom du fichier et
#: celui de la fonction fuitent l'arborescence du serveur ; le message
#: d'exception fuit ce que le code manipulait au moment de l'échec.
_FUITES = (
    "Traceback",
    "secret-de-la-base",
    "test_core_wsgi_error_path_001.py",
    "controleur_qui_leve",
)

#: Une page 500 ordinaire, telle que le squelette la livre.
_PAGE_500_VALIDE = "<!doctype html><title>Erreur</title><h1>Erreur interne</h1>"


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(path: str = "/boum", method: str = "GET") -> dict[str, Any]:
    return {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "mot_de_passe=secret-de-la-base",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "HTTP_AUTHORIZATION": "Bearer secret-de-la-base",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }


def controleur_qui_leve(request: Any):
    """Un contrôleur ordinaire qui échoue, comme n'importe lequel peut le faire."""
    raise RuntimeError("connexion refusée avec le mot de passe secret-de-la-base")


@pytest.fixture
def vues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Un dossier de vues réel, avec un moteur Jinja enregistré.

    Reproduit ce que fait `build_application` au démarrage : sans cette
    inscription, le rendu lève « Aucun renderer enregistré » et l'on mesurerait
    un défaut de montage plutôt que le comportement du framework.
    """
    racine = tmp_path / "views"
    (racine / "errors").mkdir(parents=True)
    (racine / "errors" / "500.html").write_text(_PAGE_500_VALIDE, encoding="utf-8")

    import core.forge as forge

    ancien_dossier = forge._cfg.get("views_dir")
    ancien_moteur = template_manager._renderer  # pyright: ignore[reportPrivateUsage]
    forge._cfg["views_dir"] = str(racine)
    template_manager.register(Jinja2Renderer(str(racine)))
    yield racine
    forge._cfg["views_dir"] = ancien_dossier
    template_manager._renderer = ancien_moteur  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def journal(tmp_path: Path):
    """Redirige le journal d'erreurs vers un dossier jetable."""
    from core.errors import runtime_error_logger

    dossier = tmp_path / "journal"
    dossier.mkdir()
    runtime_error_logger.set_jsonl_dir(dossier)
    yield dossier
    runtime_error_logger.set_jsonl_dir(None)


@pytest.fixture
def wsgi_app(vues: Path, journal: Path):
    router = Router()
    router.add("GET", "/boum", controleur_qui_leve, public=True, csrf=False)
    router.add("GET", "/api/boum", controleur_qui_leve, public=True, csrf=False, api=True)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


# ── Le chemin nominal de l'échec ─────────────────────────────────────────────


def test_un_controleur_qui_leve_rend_500_et_non_une_exception(wsgi_app) -> None:
    """L'exception ne doit jamais ressortir du callable WSGI.

    Si elle ressort, c'est le serveur qui répond, sans les en-têtes de sécurité
    de Forge et sans qu'aucune trace ne soit journalisée.
    """
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ(), start_response))

    assert capture["status"] is not None, (
        "aucun statut n'a été émis : l'exception a traversé le callable WSGI"
    )
    assert capture["status"].startswith("500")
    assert corps, "un corps vide laisse le navigateur sans rien à afficher"


def test_la_page_500_porte_les_entetes_de_securite(wsgi_app) -> None:
    """Une page d'erreur reste une réponse : elle ne se dispense pas du socle.

    C'est le chemin le plus facile à oublier, puisqu'il ne passe pas par le
    code nominal.
    """
    start_response, capture = _capture()
    list(wsgi_app(_environ(), start_response))

    entetes = {nom.lower() for nom, _ in capture["headers"]}

    assert "x-content-type-options" in entetes, (
        f"socle de sécurité absent de la page 500 : {sorted(entetes)}"
    )
    assert "content-type" in entetes


@pytest.mark.parametrize("fuite", _FUITES)
def test_la_page_500_ne_divulgue_rien_en_production(wsgi_app, fuite: str) -> None:
    """En production, la cause reste dans les journaux, pas dans la réponse.

    Le paramétrage nomme chaque fuite séparément : un `assert` unique sur une
    liste s'arrête à la première et masque les suivantes.
    """
    import core.forge as forge

    ancien = forge._cfg.get("app_env")
    forge._cfg["app_env"] = "prod"
    try:
        start_response, _ = _capture()
        corps = b"".join(wsgi_app(_environ(), start_response)).decode("utf-8", "replace")
    finally:
        forge._cfg["app_env"] = ancien

    assert fuite not in corps, (
        f"la page 500 divulgue « {fuite} » en production :\n{corps[:400]}"
    )


def test_une_route_api_rend_du_json_sans_detail(wsgi_app) -> None:
    """Une réponse d'API part vers un client qui la journalise ou la réexpose.

    Elle ne doit donc porter aucun détail, **même en dev**, là où la page HTML
    peut se le permettre puisqu'un humain la lit devant son navigateur.
    """
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ(path="/api/boum"), start_response))

    assert capture["status"].startswith("500")
    charge = json.loads(corps.decode("utf-8"))
    assert "secret-de-la-base" not in json.dumps(charge)
    assert "Traceback" not in json.dumps(charge)


# ── Quand la page d'erreur est elle-même en défaut ───────────────────────────


@pytest.mark.parametrize(
    ("cas", "gabarit"),
    [
        ("syntaxe Jinja invalide", "{% if %}<h1>Erreur</h1>"),
        ("filtre inconnu", "{{ 'x' | filtre_qui_nexiste_pas }}"),
        ("appel impossible sur une variable absente", "{{ absente.methode() }}"),
    ],
)
def test_une_page_500_cassee_ne_masque_pas_la_reponse(
    wsgi_app, vues: Path, cas: str, gabarit: str
) -> None:
    """LE test du ticket : `errors/500.html` appartient à l'utilisateur.

    Le squelette le livre et Forge n'y réécrit jamais (principe 4). Un projet
    peut donc le casser, et il le fait au pire moment, puisque ce gabarit ne
    sert que lorsque quelque chose a déjà échoué.

    `core.http.helpers.html` ne rattrape que `TemplateNotFoundError` : toute
    autre erreur de rendu ressort de `dispatch` et traverse le callable WSGI.
    L'exploitant voit alors l'erreur du gabarit d'erreur, et **la cause
    première est perdue**.
    """
    (vues / "errors" / "500.html").write_text(gabarit, encoding="utf-8")
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ(), start_response))

    assert capture["status"] is not None, (
        f"page 500 en défaut ({cas}) : l'exception a traversé le callable WSGI, "
        "le serveur répond à la place de Forge et la cause première est perdue"
    )
    assert capture["status"].startswith("500")
    assert corps, "un corps vide laisse le navigateur sans rien à afficher"


def test_une_page_500_absente_reste_rattrapee(wsgi_app, vues: Path) -> None:
    """Le cas déjà traité, conservé pour distinguer ce qui l'est de ce qui ne l'est pas.

    Un gabarit introuvable est rattrapé par `TemplateNotFoundError`. C'est
    précisément parce que ce cas-là fonctionne que les autres passaient
    inaperçus.
    """
    (vues / "errors" / "500.html").unlink()
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ(), start_response))

    assert capture["status"] is not None
    assert corps


def test_un_journal_inecrivable_ne_masque_pas_la_500(wsgi_app, monkeypatch) -> None:
    """Le disque plein est le cas où l'on a le plus besoin de la page d'erreur.

    `_log_runtime_error` est appelé **dans** le bloc `except` de `dispatch`.
    S'il lève, l'exception ressort et Forge perd la main sur la réponse au
    moment précis où l'exploitant a besoin qu'elle tienne.
    """
    def disque_plein(*args: Any, **kwargs: Any):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("core.app.application._log_runtime_error", disque_plein)

    start_response, capture = _capture()
    corps = b"".join(wsgi_app(_environ(), start_response))

    assert capture["status"] is not None, (
        "un journal inécrivable a fait ressortir l'exception du callable WSGI"
    )
    assert capture["status"].startswith("500")
    assert corps


def test_un_contexte_de_dev_defaillant_ne_masque_pas_la_500(wsgi_app, monkeypatch) -> None:
    """Même raisonnement pour la construction du contexte de la page de dev.

    Elle inspecte l'exception et sa pile ; un objet exotique peut l'y faire
    échouer, et ce serait alors l'exception du diagnostic que verrait
    l'utilisateur, pas la sienne.
    """
    def contexte_defaillant(*args: Any, **kwargs: Any):
        raise ValueError("introspection impossible")

    monkeypatch.setattr("core.app.application._dev_error_context", contexte_defaillant)

    start_response, capture = _capture()
    corps = b"".join(wsgi_app(_environ(), start_response))

    assert capture["status"] is not None, (
        "un contexte de dev défaillant a fait ressortir l'exception"
    )
    assert capture["status"].startswith("500")
    assert corps


# ── Ce que le journal retient ────────────────────────────────────────────────


def _evenements(journal: Path) -> list[dict[str, Any]]:
    lignes = [
        ligne
        for chemin in sorted(journal.rglob("*.jsonl"))
        for ligne in chemin.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]
    assert lignes, f"aucun événement journalisé dans {journal}"
    return [json.loads(ligne) for ligne in lignes]


def test_le_journal_masque_les_valeurs_de_la_requete(wsgi_app, journal: Path) -> None:
    """La requête est consignée par ses noms, jamais par ses valeurs.

    Le journal est un fichier lu par un humain, souvent recopié dans un ticket.
    La chaîne de requête y était écrite telle quelle, alors que c'est
    l'endroit où les jetons voyagent : lien de réinitialisation, clé d'API,
    lien magique. Un `GET` est la façon la plus courante de faire entrer un
    secret dans un journal.
    """
    start_response, _ = _capture()
    list(wsgi_app(_environ(), start_response))

    requete = _evenements(journal)[0]["request"]

    assert "secret-de-la-base" not in json.dumps(requete), (
        f"le journal porte une valeur de la requête en clair : {requete}"
    )
    assert "mot_de_passe" in requete["query"], (
        "le nom du paramètre doit rester lisible, seule sa valeur est retirée"
    )


def test_le_message_de_l_exception_est_consigne_a_dessein(wsgi_app, journal: Path) -> None:
    """La contrepartie, écrite pour qu'elle ne soit pas prise pour un oubli.

    Le message de l'exception **est** consigné : c'est la raison d'être du
    journal, et le distinguer de la requête est délibéré. Une application qui
    place un secret dans le texte de ses exceptions le verra donc dans son
    journal, et c'est à elle de ne pas le faire.

    Sans ce test, quelqu'un lisant le précédent pourrait croire que le journal
    masque tout, et durcir le masquage jusqu'à le vider de son intérêt.
    """
    start_response, _ = _capture()
    list(wsgi_app(_environ(), start_response))

    evenement = _evenements(journal)[0]

    assert evenement["exception_type"] == "RuntimeError"
    assert "connexion refusée" in evenement["message"]
