"""CRUD-DUP-HANDLING-001 — le CRUD généré traite le doublon.

Une entité pouvait déclarer un champ `unique` : le DDL créait bien la
contrainte, mais le contrôleur généré n'entourait l'INSERT pour aucun champ
unique. Un doublon soumis remontait l'exception brute du pilote et produisait
une 500, sur les quatre backends.

Le contrôleur attrape désormais `UniqueViolationError`
(`DB-UNIQUE-VIOLATION-CONTRACT-001`, portable entre backends) et réaffiche le
formulaire avec l'erreur, à la création comme à la modification.

Invariant à préserver : une entité **sans** champ unique doit produire
exactement le même contrôleur qu'avant ce ticket, sans import ni garde inutile
(principe 8, on n'émet pas de code qui ne sert à rien).
"""
from __future__ import annotations

import ast
from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.crud.controller_builder import build_controller  # noqa: E402

IMPORT_LINE = "from core.database.errors import UniqueViolationError"
GUARD_LINE = "except UniqueViolationError:"


def _definition(unique_names: set[str]) -> dict[str, Any]:
    fields: list[dict[str, Any]] = [{
        "name": "id", "column": "Id", "sql_type": "INTEGER", "python_type": "int",
        "primary_key": True, "auto_increment": True, "nullable": False, "unique": False,
    }]
    for name in ("email", "matricule", "nom"):
        fields.append({
            "name": name, "column": name.capitalize(), "sql_type": "TEXT",
            "python_type": "str", "primary_key": False, "auto_increment": False,
            "nullable": False, "unique": name in unique_names,
        })
    return {"entity": "Eleve", "table": "eleve", "fields": fields}


def _controller(unique_names: set[str]) -> str:
    return build_controller(_definition(unique_names))


# ── Le code généré reste valide ──────────────────────────────────────────────


@pytest.mark.parametrize("uniques", [set(), {"email"}, {"email", "matricule"}])
def test_controleur_genere_est_syntaxiquement_valide(uniques: set[str]) -> None:
    ast.parse(_controller(uniques))


# ── Avec un champ unique ─────────────────────────────────────────────────────


def test_import_de_lexception_portable() -> None:
    assert IMPORT_LINE in _controller({"email"})


def test_create_et_update_sont_gardes() -> None:
    """Les deux actions peuvent violer l'unicité, les deux sont couvertes."""
    source = _controller({"email"})
    assert source.count(GUARD_LINE) == 2, (
        "create ET update doivent attraper le doublon."
    )


def test_lerreur_est_posee_sur_le_champ_unique() -> None:
    source = _controller({"email"})
    assert 'form.add_error("email", "Cette valeur est déjà utilisée.")' in source


def test_le_formulaire_est_reaffiche_et_non_une_500() -> None:
    """Le garde rend le formulaire, il ne laisse pas remonter l'exception."""
    source = _controller({"email"})
    guard_at = source.index(GUARD_LINE)
    after = source[guard_at:guard_at + 600]
    assert "BaseController.validation_error" in after
    assert '"form": form,' in after


def test_plusieurs_champs_uniques_donnent_une_erreur_globale() -> None:
    """L'exception ne dit pas quelle contrainte a sauté : on n'en désigne aucune."""
    source = _controller({"email", "matricule"})
    assert "form.add_error(None," in source
    assert 'form.add_error("email"' not in source
    assert 'form.add_error("matricule"' not in source


# ── Sans champ unique : aucune régression de sortie ───────────────────────────


def test_sans_champ_unique_aucun_garde_ni_import() -> None:
    source = _controller(set())
    assert IMPORT_LINE not in source, (
        "Aucun champ unique : ne pas importer une exception jamais levee."
    )
    assert GUARD_LINE not in source, (
        "Aucun champ unique : ne pas emettre de garde inutile (principe 8)."
    )


def test_sans_champ_unique_la_persistance_reste_directe() -> None:
    source = _controller(set())
    assert "        add_eleve(form.cleaned_data)" in source
    assert "        update_eleve(id, form.cleaned_data)" in source
