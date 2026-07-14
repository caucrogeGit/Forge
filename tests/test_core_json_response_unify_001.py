"""Tests — CORE-JSON-RESPONSE-UNIFY-001 : Response.json, source unique du JSON.

Trois constructeurs sérialisaient le JSON séparément : `Response.json`,
`core.http.helpers.json_response` et `BaseController.json`. Ce dernier n'avait
pas le garde `TypeError` → `ValueError` et pouvait diverger sur le content-type.
Les deux autres délèguent désormais à `Response.json`. Ce test verrouille
l'équivalence de sortie et le garde partagé.
"""
from __future__ import annotations

import json

import pytest

from core.http.helpers import json_response
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

_DATA = {"id": 1, "nom": "Dupont", "msg": "héros"}


def _triple(data, status=200):
    return [
        Response.json(data, status),
        json_response(data, status),
        BaseController.json(data, status),
    ]


class TestEquivalence:
    def test_meme_status_content_type_body(self):
        responses = _triple(_DATA, 201)
        for resp in responses:
            assert resp.status == 201
            assert resp.content_type == "application/json; charset=utf-8"
            assert json.loads(resp.body) == _DATA

    def test_unicode_non_echappe(self):
        for resp in _triple({"msg": "héros"}):
            assert "héros" in resp.body.decode("utf-8")


class TestSharedGuard:
    @pytest.mark.parametrize("make", [
        lambda d: Response.json(d),
        lambda d: json_response(d),
        lambda d: BaseController.json(d),
    ], ids=["Response.json", "json_response", "BaseController.json"])
    def test_non_serialisable_leve_valueerror(self, make):
        # Le garde canonique (TypeError → ValueError convivial) doit valoir pour
        # les trois voies — BaseController.json ne l'avait pas avant l'unification.
        with pytest.raises(ValueError):
            make({"bad": object()})


def test_helpers_ne_reimporte_pas_json():
    # Garde-fou de source unique : helpers.py ne sérialise plus lui-même.
    import inspect

    import core.http.helpers as helpers

    source = inspect.getsource(helpers.json_response)
    assert "dumps" not in source, (
        "json_response doit déléguer à Response.json, pas resérialiser."
    )
