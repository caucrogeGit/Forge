"""CRUD-CSV-ESCAPE-CORE-001 : la neutralisation CSV vient du cœur, pas d'une copie.

`forge make:crud` **recopiait** dans chaque contrôleur une défense contre
l'injection de formule CSV. Mesuré sur une application réelle de 50 entités :
36 exemplaires identiques de la même fonction.

Deux défauts en un. La règle était **incomplète** : elle ne regardait que le
premier caractère, alors qu'un tableur ignore une tabulation ou un retour
chariot de tête, si bien que `"\\t=1+1"` s'ouvrait comme la formule `=1+1`.
Et surtout elle était **incorrigible** : Forge ne réécrit jamais le code
utilisateur (principe 9), donc une correction n'aurait jamais atteint les
fichiers déjà générés.

La règle vit désormais dans `core.security.csv_export`. Le contrôleur généré
l'appelle. Un `pip install --upgrade` suffit à corriger toutes les applications.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.security.csv_export import (
    FORMULA_TRIGGERS,
    INVISIBLE_LEADERS,
    escape_csv_field,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── La primitive ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("trigger", FORMULA_TRIGGERS)
def test_chaque_declencheur_de_formule_est_neutralise(trigger: str) -> None:
    assert escape_csv_field(f"{trigger}1+1") == f"'{trigger}1+1"


@pytest.mark.parametrize("leader", INVISIBLE_LEADERS)
@pytest.mark.parametrize("trigger", FORMULA_TRIGGERS)
def test_un_caractere_invisible_ne_masque_plus_le_declencheur(
    leader: str, trigger: str,
) -> None:
    """Le contournement que l'ancienne règle laissait passer."""
    value = f"{leader}{trigger}SUM(A1)"
    assert escape_csv_field(value) == f"'{value}"


@pytest.mark.parametrize(
    "value",
    ["Dupont", "", "a=1", "1+1", "  =1+1", "\tDupont", "élève"],
)
def test_une_valeur_inoffensive_est_rendue_telle_quelle(value: str) -> None:
    """Le cas courant : aucune valeur ne doit être abîmée."""
    assert escape_csv_field(value) == value


def test_aucun_caractere_n_est_retire_ni_remplace() -> None:
    """La valeur d'origine reste lisible : on préfixe, on ne mutile pas."""
    neutralisee = escape_csv_field("=1+1")
    assert neutralisee.endswith("=1+1")
    assert neutralisee == "'" + "=1+1"


# ── Le contrat avec le générateur ────────────────────────────────────────────

def _generated_controller() -> str:
    from forge_mvc_entities.crud.controller_builder import build_controller

    definition = {
        "entity": "Article",
        "table": "articles",
        "fields": [
            {
                "name": "id", "column": "Id", "sql_type": "BIGINT UNSIGNED",
                "python_type": "int", "primary_key": True,
                "auto_increment": True, "nullable": False,
            },
            {
                "name": "titre", "column": "Titre", "sql_type": "VARCHAR(255)",
                "python_type": "str", "forge_type": "string", "nullable": False,
            },
        ],
    }
    return build_controller(definition)


def test_le_controleur_genere_appelle_la_primitive_du_coeur() -> None:
    source = _generated_controller()

    assert "from core.security.csv_export import escape_csv_field" in source
    assert "escape_csv_field(str(row.get(key)" in source


def test_le_controleur_genere_ne_recopie_plus_la_regle() -> None:
    source = _generated_controller()

    assert "_csv_escape" not in source, "la règle est de nouveau recopiée"
    assert '("=", "+", "-", "@")' not in source


def test_le_controleur_genere_reste_du_python_valide() -> None:
    ast.parse(_generated_controller())


# ── Garde-fou de cause : plus aucune primitive de sécurité recopiée ──────────

SECURITY_LITERALS = (
    '("=", "+", "-", "@")',  # neutralisation CSV
)

GENERATOR_ROOTS = (
    "packages/forge-mvc-entities/forge_mvc_entities",
    "cli",
)


@pytest.mark.parametrize("relative", GENERATOR_ROOTS)
def test_aucun_generateur_ne_recopie_une_primitive_de_securite(relative: str) -> None:
    """Une règle de sécurité s'appelle, elle ne se recopie pas.

    Ce qu'un générateur **écrit** dans le projet devient du code utilisateur,
    que Forge s'interdit de retoucher. Une primitive de sécurité doit donc vivre
    dans le cœur ou dans un opt-in, et le code généré doit l'importer.
    """
    offenders: list[str] = []
    for path in (PROJECT_ROOT / relative).rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for literal in SECURITY_LITERALS:
            if literal in text:
                offenders.append(f"{path.relative_to(PROJECT_ROOT)} : {literal}")

    assert offenders == [], (
        "Un générateur recopie une primitive de sécurité au lieu de l'appeler ; "
        f"elle deviendrait incorrigible dans les projets générés : {offenders}"
    )
