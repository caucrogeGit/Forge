"""Garde-fou CORE-ROUTE-HANDLER-CALLABLE-001 (retour terrain, ADR-009).

Même classe de bug que `CORE-RESPONSE-STATUS-TYPE-001` : un argument critique
non validé provoque une erreur **différée**. Ici, un handler de route non
appelable ne cassait qu'au dispatch (`route.handler(request)`), avec un traceback
pointant le routeur et non la ligne de `mvc/routes.py` fautive.

La route valide désormais le handler **à l'enregistrement** (donc à l'import de
`routes.py`) : `TypeError` explicite, traceback sur la bonne ligne.
"""
from __future__ import annotations

import pytest

from core.http.router import Router


def _ok(request):
    return None


def test_handler_non_appelable_leve_typeerror_a_l_enregistrement():
    router = Router()
    with pytest.raises(TypeError):
        router.add("GET", "/", "pas_appelable")


def test_message_est_actionnable():
    router = Router()
    with pytest.raises(TypeError) as exc:
        router.add("GET", "/", 42)
    msg = str(exc.value)
    assert "handler" in msg
    assert "appelable" in msg
    assert "HomeController.index" in msg, "Le message doit donner un exemple correct."


def test_handler_appelable_accepte():
    router = Router()
    router.add("GET", "/", _ok, name="home")
    assert router.url_for("home") == "/"


def test_validation_aussi_dans_un_groupe():
    router = Router()
    with router.group("", public=True) as public:
        with pytest.raises(TypeError):
            public.add("GET", "/x", None)
