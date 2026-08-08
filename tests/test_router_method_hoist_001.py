"""ROUTER-METHOD-HOIST-001 : le dégraissage des boucles ne change rien au sens.

Le ticket sort la normalisation de méthode des boucles de résolution et
supprime l'appel de fonction Python par entrée parcourue. Mesuré, ces appels
coûtaient plus que les expressions rationnelles qu'ils encadraient : la
résolution y gagne 41 à 47 % sur le chemin nominal.

Un ticket de performance ne se juge pas à son gain mais à ce qu'il n'a pas
cassé. Ces tests verrouillent donc la **sémantique**, cas par cas, y compris
les deux pièges du remaniement.

Premier piège, `RouteEntry.methods` est un `frozenset`, donc sans ordre.
`method_label` doit continuer de lire `self.method`, qui garde l'ordre de
déclaration, sans quoi `routes:list` afficherait « POST,GET » au hasard.

Second piège, `is_public()` teste désormais `public` avant l'expression
rationnelle. L'ordre des tests change, le résultat non.

Le banc de mesure vit dans `tools/bench_router.py`, pour que le chiffre du
changelog reste contredisable.
"""
from __future__ import annotations

import pytest

from core.http.router import RouteEntry, Router


def _handler(request: object) -> None:
    return None


# ── Les méthodes précalculées disent la même chose que la déclaration ────────


@pytest.mark.parametrize(
    ("declare", "attendu"),
    [
        ("GET", {"GET"}),
        ("get", {"GET"}),
        (["GET", "POST"], {"GET", "POST"}),
        (["get", "Post"], {"GET", "POST"}),
    ],
)
def test_les_methodes_precalculees_couvrent_la_declaration(
    declare: str | list[str], attendu: set[str]
) -> None:
    entree = RouteEntry(declare, "/x", _handler)

    assert entree.methods == frozenset(attendu)


@pytest.mark.parametrize("methode", ["GET", "get", "GeT"])
def test_matches_method_reste_insensible_a_la_casse(methode: str) -> None:
    entree = RouteEntry("GET", "/x", _handler)

    assert entree.matches_method(methode) is True
    assert entree.matches_method("POST") is False


def test_le_libelle_garde_l_ordre_de_declaration() -> None:
    """Le piège du frozenset : sans ordre, `routes:list` afficherait au hasard."""
    entree = RouteEntry(["POST", "GET"], "/x", _handler)

    assert entree.method_label == "POST,GET"


# ── La résolution rend les mêmes routes qu'avant ─────────────────────────────


def test_la_resolution_est_insensible_a_la_casse_de_la_methode() -> None:
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="client-index")

    for methode in ("GET", "get", "GeT"):
        resultat = routeur.match(methode, "/client/index")
        assert resultat is not None, methode
        assert resultat[0].name == "client-index"


def test_une_route_multi_methodes_repond_a_chacune() -> None:
    routeur = Router()
    routeur.add(["GET", "POST"], "/contact/form", _handler, name="contact-form")

    assert routeur.match("GET", "/contact/form") is not None
    assert routeur.match("POST", "/contact/form") is not None
    assert routeur.match("DELETE", "/contact/form") is None


def test_les_parametres_captures_sont_inchanges() -> None:
    routeur = Router()
    routeur.add("GET", "/client/show/{id}", _handler, name="client-show")

    resultat = routeur.match("GET", "/client/show/42")

    assert resultat is not None
    assert resultat[1] == {"id": "42"}


def test_une_route_statique_ne_capture_rien() -> None:
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="client-index")

    resultat = routeur.match("GET", "/client/index")

    assert resultat is not None
    assert resultat[1] == {}


def test_la_premiere_route_declaree_gagne_toujours() -> None:
    """Contrat d'ordre inchangé par ce ticket.

    Il n'est ni écrit ni voulu, il découle de l'ordre d'itération. Le fixer ici
    garantit qu'il ne bougera pas **par accident** : le ticket qui le changera
    devra faire échouer ce test, donc le dire.
    """
    routeur = Router()
    routeur.add("GET", "/client/{id}", _handler, name="dynamique")
    routeur.add("GET", "/client/index", _handler, name="statique")

    resultat = routeur.match("GET", "/client/index")

    assert resultat is not None
    assert resultat[0].name == "dynamique"
    assert resultat[1] == {"id": "index"}


# ── Les méthodes autorisées restent agrégées, toutes routes confondues ───────


def test_allowed_methods_agrege_toutes_les_entrees_du_chemin() -> None:
    """Le contrat de `CORE-HTTP-405-ALLOW-001` : l'en-tête `Allow` est exhaustif."""
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="a")
    routeur.add("POST", "/client/index", _handler, name="b")
    routeur.add(["PUT", "PATCH"], "/client/index", _handler, name="c")

    assert routeur.allowed_methods("/client/index") == ["GET", "PATCH", "POST", "PUT"]


def test_allowed_methods_est_vide_sur_un_chemin_inconnu() -> None:
    """C'est ce vide qui distingue un 404 d'un 405."""
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="a")

    assert routeur.allowed_methods("/inconnu") == []


def test_allowed_methods_suit_aussi_les_routes_dynamiques() -> None:
    routeur = Router()
    routeur.add("GET", "/client/show/{id}", _handler, name="a")
    routeur.add("POST", "/client/show/{id}", _handler, name="b")

    assert routeur.allowed_methods("/client/show/42") == ["GET", "POST"]


# ── is_public : l'ordre des tests change, le résultat non ────────────────────


def test_is_public_sans_methode() -> None:
    routeur = Router()
    routeur.add("GET", "/login/form", _handler, name="a", public=True)
    routeur.add("GET", "/admin/index", _handler, name="b")

    assert routeur.is_public("/login/form") is True
    assert routeur.is_public("/admin/index") is False
    assert routeur.is_public("/inconnu") is False


def test_is_public_avec_methode() -> None:
    routeur = Router()
    routeur.add("GET", "/contact/form", _handler, name="a", public=True)
    routeur.add("POST", "/contact/form", _handler, name="b", public=False)

    assert routeur.is_public("/contact/form", "GET") is True
    assert routeur.is_public("/contact/form", "POST") is False


def test_is_public_est_insensible_a_la_casse() -> None:
    routeur = Router()
    routeur.add("GET", "/login/form", _handler, name="a", public=True)

    assert routeur.is_public("/login/form", "get") is True


# ── L'ordre de déclaration reste celui de `iter_routes` ──────────────────────


def test_iter_routes_garde_l_ordre_de_declaration() -> None:
    """`routes:list` en dépend : un affichage réordonné serait illisible."""
    routeur = Router()
    for nom in ("un", "deux", "trois"):
        routeur.add("GET", f"/{nom}", _handler, name=nom)

    assert [e.name for e in routeur.iter_routes()] == ["un", "deux", "trois"]
