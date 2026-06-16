"""Garde-fou méta CORE-EARLY-VALIDATION-CONTRACT-001 (convention C.6, ADR-009).

Contrat : les entrées publiques du cœur appelées par le code applicatif
(contrôleur, `mvc/routes.py`, boot) valident **tôt** leurs arguments positionnels
critiques avec un `TypeError` actionnable, au lieu de laisser passer une valeur
invalide qui ne casserait que plus loin (erreur **différée**).

Ce fichier est le **registre** du contrat : une entrée par ligne dans `CONTRACT`.
Quand on couvre une nouvelle entrée du cœur (cf. `conventions.md` C.6), ajouter
sa ligne ici. Issu des retours de tests terrain, cycle b17.
"""
from __future__ import annotations

import pytest

from core.http.helpers import html
from core.http.response import Response
from core.http.router import Router
from core.mvc.controller.base_controller import BaseController

pytestmark = pytest.mark.meta


def _response_status_str():
    Response("texte au lieu du status")


def _html_status_dict():
    html("home/index.html", {"contexte": "au lieu du status"})


def _render_status_dict():
    BaseController.render("home/index.html", {"contexte": "au lieu du status"})


def _route_handler_non_callable():
    Router().add("GET", "/", "pas_appelable")


# Registre du contrat : (libellé, appel fautif attendu en TypeError).
CONTRACT = [
    pytest.param(_response_status_str, id="Response(status)"),
    pytest.param(_html_status_dict, id="html(status)"),
    pytest.param(_render_status_dict, id="render(status)"),
    pytest.param(_route_handler_non_callable, id="router.add(handler)"),
]


@pytest.mark.parametrize("call", CONTRACT)
def test_validation_precoce_leve_typeerror(call):
    with pytest.raises(TypeError):
        call()
