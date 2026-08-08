"""ROUTER-STATIC-INDEX-001 : le routeur indexe ses routes statiques.

Le gain de vitesse n'est pas le motif principal de ce ticket, et le dire
autrement serait mentir sur son urgence : une route statique passe de 57 à
0,3 microseconde à mille routes, échelle qu'aucune application Forge n'atteint.

Le vrai motif est que Forge n'avait **aucune règle de résolution écrite**. Le
résultat découlait de l'ordre d'itération d'une liste, si bien que déclarer
`/client/{id}` avant `/client/index` faisait résoudre `/client/index` vers
`show(id="index")`. Le contrôleur recevait un identifiant nommé « index », et
le développeur y lisait une erreur de base de données, jamais une erreur de
routage. Une règle qui dépend de l'ordre des lignes d'un fichier et que
personne n'a énoncée est de la magie cachée (principe 3).

La règle est désormais : **une route statique l'emporte sur une route
dynamique**, quel que soit l'ordre de déclaration ; entre deux routes de même
nature, la première déclarée gagne.

Ces tests verrouillent la règle, la partition qui la met en œuvre, et le piège
de classement qui rendrait une route introuvable.
"""
from __future__ import annotations

import pytest

from core.http.router import RouteEntry, Router


def _handler(request: object) -> None:
    return None


# ── Le classement statique / dynamique ───────────────────────────────────────


@pytest.mark.parametrize(
    ("motif", "statique"),
    [
        ("/client/index", True),
        ("/", True),
        ("", True),
        ("/client/show/{id}", False),
        ("/{id}", False),
        ("/a/{x}/b/{y}", False),
        # Le piège. Le tiret n'appartient pas à `\w`, donc `{id-x}` n'est pas un
        # paramètre : le segment est échappé littéralement et la route est
        # STATIQUE. Un classement par « le motif contient une accolade » la
        # rangerait parmi les dynamiques, où le dictionnaire ne la chercherait
        # jamais : elle deviendrait introuvable.
        ("/a/{id-x}", True),
        ("/a/{}", True),
        ("/a/{ }", True),
    ],
)
def test_le_classement_suit_le_critere_de_compilation(motif: str, statique: bool) -> None:
    assert RouteEntry("GET", motif, _handler).is_static is statique


def test_une_route_au_motif_trompeur_reste_resolvable() -> None:
    """Le piège précédent, vérifié de bout en bout et pas seulement sur le drapeau."""
    routeur = Router()
    routeur.add("GET", "/a/{id-x}", _handler, name="litterale")

    resultat = routeur.match("GET", "/a/{id-x}")

    assert resultat is not None
    assert resultat[0].name == "litterale"
    assert resultat[1] == {}


# ── La règle de résolution ───────────────────────────────────────────────────


def test_le_statique_l_emporte_meme_declare_apres() -> None:
    """LE test du ticket : c'est le cas qui a changé de résultat."""
    routeur = Router()
    routeur.add("GET", "/client/{id}", _handler, name="dynamique")
    routeur.add("GET", "/client/index", _handler, name="statique")

    resultat = routeur.match("GET", "/client/index")

    assert resultat is not None
    assert resultat[0].name == "statique"
    assert resultat[1] == {}


def test_le_statique_l_emporte_aussi_declare_avant() -> None:
    """La règle ne doit pas dépendre de l'ordre, sinon elle n'en est pas une."""
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="statique")
    routeur.add("GET", "/client/{id}", _handler, name="dynamique")

    resultat = routeur.match("GET", "/client/index")

    assert resultat is not None
    assert resultat[0].name == "statique"


def test_la_dynamique_sert_toujours_ce_que_la_statique_ne_couvre_pas() -> None:
    routeur = Router()
    routeur.add("GET", "/client/{id}", _handler, name="dynamique")
    routeur.add("GET", "/client/index", _handler, name="statique")

    resultat = routeur.match("GET", "/client/42")

    assert resultat is not None
    assert resultat[0].name == "dynamique"
    assert resultat[1] == {"id": "42"}


def test_entre_deux_statiques_la_premiere_declaree_gagne() -> None:
    routeur = Router()
    routeur.add("GET", "/x", _handler, name="premiere")
    routeur.add("GET", "/x", _handler, name="seconde")

    resultat = routeur.match("GET", "/x")

    assert resultat is not None
    assert resultat[0].name == "premiere"


def test_un_chemin_statique_porte_plusieurs_methodes() -> None:
    """La valeur du dictionnaire est une liste, pas une entrée unique."""
    routeur = Router()
    routeur.add("GET", "/contact/form", _handler, name="form")
    routeur.add("POST", "/contact/form", _handler, name="envoi")

    assert routeur.match("GET", "/contact/form")[0].name == "form"       # pyright: ignore[reportOptionalSubscript]
    assert routeur.match("POST", "/contact/form")[0].name == "envoi"     # pyright: ignore[reportOptionalSubscript]
    assert routeur.match("DELETE", "/contact/form") is None


def test_une_methode_absente_du_statique_retombe_sur_le_dynamique() -> None:
    """Le dictionnaire ne doit pas court-circuiter la recherche quand il échoue.

    Sortir après un chemin statique trouvé mais sans la bonne méthode
    masquerait une route dynamique parfaitement valide.
    """
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="statique-get")
    routeur.add("POST", "/client/{id}", _handler, name="dynamique-post")

    resultat = routeur.match("POST", "/client/index")

    assert resultat is not None
    assert resultat[0].name == "dynamique-post"
    assert resultat[1] == {"id": "index"}


# ── La partition reste fidèle au tableau de routes ───────────────────────────


def test_la_partition_couvre_exactement_les_routes_declarees() -> None:
    """Une entrée absente des deux structures serait introuvable en silence."""
    routeur = Router()
    routeur.add("GET", "/a/index", _handler, name="a")
    routeur.add("GET", "/a/show/{id}", _handler, name="b")
    routeur.add("POST", "/a/index", _handler, name="c")
    routeur.add("GET", "/", _handler, name="d")

    indexees = [e for entrees in routeur._static.values() for e in entrees]  # pyright: ignore[reportPrivateUsage]
    indexees += routeur._dynamic                                            # pyright: ignore[reportPrivateUsage]

    assert sorted(e.name or "" for e in indexees) == ["a", "b", "c", "d"]
    assert len(indexees) == len(routeur.iter_routes())


def test_iter_routes_garde_l_ordre_de_declaration() -> None:
    """La partition est une vue : elle ne doit pas devenir la source d'ordre."""
    routeur = Router()
    routeur.add("GET", "/z/show/{id}", _handler, name="un")
    routeur.add("GET", "/a/index", _handler, name="deux")
    routeur.add("GET", "/m/show/{id}", _handler, name="trois")

    assert [e.name for e in routeur.iter_routes()] == ["un", "deux", "trois"]


def test_les_groupes_alimentent_aussi_la_partition() -> None:
    """Les routes déclarées par groupe passent par `add()`, donc sont indexées."""
    routeur = Router()
    with routeur.group("/client", public=True) as g:
        g.add("GET", "/index", _handler, name="client-index")
        g.add("GET", "/show/{id}", _handler, name="client-show")

    assert routeur.match("GET", "/client/index")[0].name == "client-index"   # pyright: ignore[reportOptionalSubscript]
    assert routeur.match("GET", "/client/show/7")[1] == {"id": "7"}          # pyright: ignore[reportOptionalSubscript]


# ── Les autres parcours suivent la même partition ────────────────────────────


def test_allowed_methods_agrege_le_statique_et_le_dynamique() -> None:
    """L'en-tête `Allow` doit rester exhaustif (CORE-HTTP-405-ALLOW-001)."""
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="a")
    routeur.add("POST", "/client/{id}", _handler, name="b")
    routeur.add("PUT", "/client/index", _handler, name="c")

    assert routeur.allowed_methods("/client/index") == ["GET", "POST", "PUT"]


def test_allowed_methods_reste_vide_sur_un_chemin_inconnu() -> None:
    routeur = Router()
    routeur.add("GET", "/client/index", _handler, name="a")

    assert routeur.allowed_methods("/inconnu/vraiment") == []


def test_is_public_voit_le_statique_et_le_dynamique() -> None:
    routeur = Router()
    routeur.add("GET", "/login/form", _handler, name="a", public=True)
    routeur.add("GET", "/public/show/{id}", _handler, name="b", public=True)
    routeur.add("GET", "/admin/index", _handler, name="c")

    assert routeur.is_public("/login/form") is True
    assert routeur.is_public("/public/show/9") is True
    assert routeur.is_public("/admin/index") is False


def test_is_public_ne_confond_pas_deux_entrees_du_meme_chemin() -> None:
    """Un chemin statique peut être public en GET et protégé en POST."""
    routeur = Router()
    routeur.add("GET", "/contact/form", _handler, name="a", public=True)
    routeur.add("POST", "/contact/form", _handler, name="b", public=False)

    assert routeur.is_public("/contact/form", "GET") is True
    assert routeur.is_public("/contact/form", "POST") is False
