"""NO-STORE-TWIN-DIVERGENCE-001 — `Cache-Control: no-store` n'existe que côté dev.

Le serveur de développement pose `Cache-Control: no-store` sur `/login`,
`/login/mfa` et `/logout`. L'adaptateur WSGI ne le pose pas : le déploiement de
production sert donc ces pages sans, et un navigateur peut les conserver dans
son cache local.

Trois pages de documentation en disaient trois choses différentes : l'une
l'annonçait automatique en production, l'autre le listait comme une dette
ouverte, la troisième l'attribuait correctement à `app.py` sans avertir que la
production ne passe pas par ce fichier.

## Pourquoi ce fichier ne corrige pas le code

Le cas diffère du nonce CSP, où le cœur pouvait simplement faire ce que faisait
déjà son jumeau. Ici il ne le peut pas : `/login` est une route **publique**,
donc indiscernable d'une page ordinaire par le contrat de route. La liste de
chemins vit dans le squelette, et l'ADR-044 l'y a mise délibérément, la
qualifiant de comportement de projet plutôt que de garantie du framework.

Fermer l'écart demande donc une décision d'API, un drapeau de route par
exemple, qui ne se prend pas au détour d'un pré-mortem. Ce fichier fixe l'état
mesuré pour que la documentation cesse de promettre ce qui n'existe pas, et
pour que le jour où la décision sera prise, le test change avec elle.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

import ast
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

#: Les chemins que le serveur de développement traite à part.
CHEMINS_AUTH = ("/login", "/login/mfa", "/logout")


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(path: str) -> dict[str, Any]:
    return {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }


def _entetes(path: str) -> dict[str, str]:
    from core.app.application import Application
    from core.app.wsgi import create_wsgi_app
    from core.http.response import Response
    from core.http.router import Router

    router = Router()
    for chemin in CHEMINS_AUTH:
        router.add("GET", chemin, lambda _r: Response(200, "ok"), public=True, csrf=False)
    app = create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))

    start_response, capture = _capture()
    list(app(_environ(path), start_response))
    return {nom.lower(): valeur for nom, valeur in capture["headers"]}


@pytest.mark.parametrize("chemin", CHEMINS_AUTH)
def test_l_adaptateur_wsgi_ne_pose_pas_no_store(chemin: str) -> None:
    """L'état mesuré, fixé pour que la documentation cesse de le contredire.

    Ce test **passe sur un défaut**, ce qui est inhabituel et mérite d'être
    dit. Il ne valide pas le comportement : il l'enregistre, faute de pouvoir
    le corriger sans décider d'une API. Le jour où Forge tranchera, il échouera
    et devra être réécrit, ce qui est exactement le signal attendu.
    """
    entetes = _entetes(chemin)

    assert "no-store" not in entetes.get("cache-control", ""), (
        f"l'adaptateur WSGI pose désormais `no-store` sur {chemin} : c'est une "
        "amélioration, et la documentation doit être remise à jour avec elle "
        "(docs/deployment/production-security.md, docs/reference/audit-auth.md, "
        "docs/features/auth.md)"
    )


def test_le_serveur_de_dev_pose_no_store() -> None:
    """L'autre jumeau, dont le comportement est le bon.

    Relevé sur l'arbre syntaxique du squelette, le serveur n'étant pas
    démarrable ici.
    """
    source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)

    litteraux = {
        element.value
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.Set)
        for element in noeud.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    }

    for chemin in CHEMINS_AUTH:
        assert chemin in litteraux, (
            f"{chemin} ne figure plus dans la liste no-store du serveur de "
            "développement ; la documentation le promet encore"
        )
    assert "no-store" in source


def test_la_documentation_ne_promet_plus_no_store_en_production() -> None:
    """Trois pages en disaient trois choses différentes.

    L'une l'annonçait automatique en production, l'autre le listait comme une
    dette ouverte, la troisième l'attribuait à `app.py` sans dire que la
    production ne passe pas par ce fichier.
    """
    page = PROJECT_ROOT / "docs" / "deployment" / "production-security.md"
    texte = page.read_text(encoding="utf-8")

    assert "serveur de développement" in texte, (
        "la page de sécurité en production doit dire d'où vient `no-store`"
    )
    assert "Absent du déploiement de production" in texte, (
        "l'absence en production doit être signalée là où l'exploitant la lit"
    )
