"""Garde-fou CORE-RENDER-STATUS-TYPE-001 (retour terrain, ADR-009).

Même classe de bug que `CORE-RESPONSE-STATUS-TYPE-001`, sur le funnel
`core.http.helpers.html()` — utilisé par `BaseController.render()` et les
helpers d'erreur. Le 2e argument positionnel est le STATUS, pas le contexte ;
`render("tpl", {...})` (réflexe d'autres frameworks) mettait un dict dans
`status` et provoquait une erreur différée et obscure.

`html()` valide désormais le `status` dès l'entrée, avec un message qui oriente
vers `context=...`.
"""
from __future__ import annotations

import pytest

from core.http.helpers import html
from core.mvc.controller.base_controller import BaseController


def test_html_status_dict_leve_typeerror():
    with pytest.raises(TypeError) as exc:
        html("home/index.html", {"x": 1})
    msg = str(exc.value)
    assert "status" in msg.lower()
    assert "context=" in msg, "Le message doit orienter vers context=…"


def test_html_status_chaine_leve_typeerror():
    with pytest.raises(TypeError):
        html("home/index.html", "200")


def test_render_delegue_la_garde():
    # render(template, status, context, ...) : 2e positionnel = status.
    # request=None → render ne fait pas de pré-traitement et délègue à html().
    with pytest.raises(TypeError):
        BaseController.render("home/index.html", {"x": 1})
