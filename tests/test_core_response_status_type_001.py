"""Garde-fou CORE-RESPONSE-STATUS-TYPE-001 (retour terrain, ADR-009).

`Response(status, body, ...)` : le 1er argument positionnel est le STATUS.
Écrire `Response("du texte")` mettait silencieusement une chaîne dans `status`
(aucune validation), puis provoquait une erreur **différée** et cryptique au
moment de l'envoi (`%d format: a real number is required, not str`) — sans jamais
pointer le contrôleur fautif dans le traceback.

La correction valide le type **dans `__init__`** : l'erreur est désormais levée
**au moment de la construction** (donc dans le frame du contrôleur appelant, qui
apparaît dans le traceback) et porte un message actionnable. Couvre tous les
chemins d'envoi (serveur de dev ET WSGI), contrairement à un garde-fou local
dans `app.py`.
"""
from __future__ import annotations

import pytest

from core.http.response import Response


def test_status_chaine_leve_typeerror():
    with pytest.raises(TypeError):
        Response("Welcome to the MVC application!")


def test_message_est_actionnable():
    with pytest.raises(TypeError) as exc:
        Response("du texte")
    msg = str(exc.value)
    assert "status" in msg
    assert "Response.text" in msg, "Le message doit orienter vers Response.text(...)."


def test_status_entier_valide():
    assert Response(200).status == 200
    assert Response(404, b"x").status == 404


def test_constructeurs_nommes_inchanges():
    assert Response.text("bonjour").status == 200
    assert Response.text("oops", status=500).status == 500


def test_bool_refuse():
    # bool est un sous-type d'int mais n'est pas un code HTTP valide.
    with pytest.raises(TypeError):
        Response(True)
