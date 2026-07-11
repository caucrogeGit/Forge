"""Garde-fou MAKE-PUBLIC-ENTITIES-GATING-001 (audit charte, ADR-070).

make:public-list/show/form lisent le contrat d'entité via forge-mvc-entities.
Sans l'opt-in, ils doivent échouer avec un message d'installation clair (cli_fail
-> SystemExit), pas une traceback brute d'import (principes 8 et 10).
"""
from __future__ import annotations

import importlib.util

import pytest

from cli.public import public_form, public_list


@pytest.mark.parametrize("call", [
    lambda: public_list.main(["Contact"]),
    lambda: public_list.show_main(["Contact"]),
    lambda: public_form.main(["Contact"]),
])
def test_make_public_fails_gracefully_without_entities(monkeypatch, capsys, call):
    # Simule l'absence du moteur d'entités.
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a, **k: None)
    with pytest.raises(SystemExit):
        call()
    captured = capsys.readouterr()
    assert "forge-mvc-entities" in (captured.out + captured.err)


def test_guard_noop_when_entities_present():
    """Le garde-fou ne fait rien quand le moteur est installé (pas d'exception)."""
    pytest.importorskip("forge_mvc_entities")
    public_list._require_entities_module()  # ne doit pas lever
