"""ENTITIES-NON-INTERACTIVE-001 : décrire une entité entière sans terminal.

`make:entity --no-input` ne posait qu'une entité minimale, aux champs imposés.
Décrire ses propres champs exigeait donc un humain devant un dialogue, ce qui
mettait hors d'atteinte le script, l'intégration continue et l'agent, alors que
Forge écrit lui-même la guidance des agents (ADR-047).

Constaté en jouant le parcours des fixtures, dont le palier « fixtures reliées »
suppose une entité portant une clé étrangère, impossible à créer autrement qu'à
la main.

Le mode non interactif devient l'égal exact du dialogue : mêmes attributs, mêmes
défauts, même validation. Les défauts comptent autant que la surface, sans quoi
les deux modes produiraient des entités différentes pour la même intention.

Deux types manquaient au générateur, tous deux adossés à un ADR. `slug` est
canonique depuis l'ADR-017, `foreign_key` est un champ de première classe depuis
l'ADR-069. La liste vivait en dur dans le générateur et avait dérivé, douze
types contre quatorze au schéma ; elle est désormais lue du schéma canonique
(ADR-058), seule façon de ne plus diverger.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.make_entity import (
    FORGE_TYPES,
    build_entity_json_from_specs,
    parse_field_spec,
)


# ── La liste des types ───────────────────────────────────────────────────────

def test_les_types_viennent_du_schema_canonique() -> None:
    """Recopiée, elle avait perdu deux types en route."""
    import json
    from pathlib import Path

    import cli.schemas

    chemin = cli.schemas.__file__
    assert chemin is not None
    schema = json.loads(
        (Path(chemin).resolve().parent / "field.schema.json").read_text(encoding="utf-8"))

    assert list(FORGE_TYPES) == schema["properties"]["type"]["enum"]


@pytest.mark.parametrize("forge_type", ["slug", "foreign_key"])
def test_les_deux_types_oublies_sont_la(forge_type: str) -> None:
    """`slug` vient de l'ADR-017, `foreign_key` de l'ADR-069."""
    assert forge_type in FORGE_TYPES


# ── Les défauts sont ceux du dialogue ────────────────────────────────────────

def test_un_champ_minimal_prend_les_defauts_du_dialogue() -> None:
    champ = parse_field_spec("nom:string")

    assert champ == {"name": "nom", "type": "string",
                     "required": True, "nullable": False, "unique": False}


@pytest.mark.parametrize(("spec", "cle", "valeur"), [
    ("nom:string:optional", "required", False),
    ("nom:string:nullable", "nullable", True),
    ("nom:string:unique", "unique", True),
    ("nom:string:max_length=120", "max_length", 120),
])
def test_chaque_attribut_est_reconnu(spec: str, cle: str, valeur: object) -> None:
    assert parse_field_spec(spec)[cle] == valeur


def test_les_attributs_se_cumulent() -> None:
    champ = parse_field_spec("nom:string:optional,nullable,unique,max_length=60")

    assert champ["required"] is False
    assert champ["nullable"] is True
    assert champ["unique"] is True
    assert champ["max_length"] == 60


# ── Ce que le dialogue exige, la ligne de commande l'exige aussi ─────────────

def test_un_decimal_sans_precision_est_refuse() -> None:
    """Le dialogue les demande toutes deux : les rendre optionnelles ici
    laisserait passer un contrat que l'autre mode interdit."""
    with pytest.raises(ValueError, match="precision"):
        parse_field_spec("montant:decimal")


def test_une_cle_etrangere_sans_cible_est_refusee() -> None:
    with pytest.raises(ValueError, match="references"):
        parse_field_spec("classe_id:foreign_key")


def test_une_cle_etrangere_nomme_son_entite_cible() -> None:
    champ = parse_field_spec("classe_id:foreign_key:references=Classe")

    assert champ["type"] == "foreign_key"
    assert champ["references"] == "Classe"


# ── Les refus disent quoi corriger ───────────────────────────────────────────

@pytest.mark.parametrize(("spec", "attendu"), [
    ("nom", "Champ mal forme"),
    ("nom:licorne", "Type invalide"),
    (":string", "Champ sans nom"),
    ("nom:string:inconnu", "Attribut inconnu"),
    ("nom:string:max_length=beaucoup", "attend un entier"),
])
def test_un_refus_nomme_le_probleme(spec: str, attendu: str) -> None:
    with pytest.raises(ValueError, match=attendu):
        parse_field_spec(spec)


# ── L'entité complète ────────────────────────────────────────────────────────

def test_l_entite_produite_a_la_forme_du_dialogue() -> None:
    entite = build_entity_json_from_specs(
        "Eleve", table="eleves",
        field_specs=["nom:string:max_length=120", "classe_id:foreign_key:references=Classe"],
        timestamps=True, soft_delete=False,
    )

    assert entite["schema_version"] == "1.0"
    assert entite["name"] == "Eleve"
    assert entite["table"] == "eleves"
    assert [c["name"] for c in entite["fields"]] == ["nom", "classe_id"]
    assert entite["options"] == {"timestamps": True, "soft_delete": False}


def test_la_table_suit_la_convention_si_on_se_tait() -> None:
    entite = build_entity_json_from_specs(
        "AnneeScolaire", table=None, field_specs=["nom:string"],
        timestamps=False, soft_delete=False)

    assert entite["table"] == "annee_scolaire"
