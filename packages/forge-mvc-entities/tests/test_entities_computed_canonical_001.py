"""`ENTITIES-COMPUTED-CANONICAL-001` — un champ calculé se déclare enfin.

`ENTITIES-COMPUTED-FIELDS-001` avait livré les champs calculés, et son test les
déclarait au **format interne V1** (`column`, `sql_type`, `python_type`), celui
qu'ADR-086 élimine. Le vert du ticket ne disait donc rien du chemin qu'empruntent
les applications.

Mesuré sur le chemin canonique, la chaîne était rompue en trois endroits.

- `field.schema.json` porte `additionalProperties: false` et ne déclarait pas
  `computed` : `forge entity:validate` refusait le contrat.
- Le résolveur de champs laissait tomber l'expression : le champ ressortait en
  colonne ordinaire.
- `make:crud` engendrait alors un `INSERT` et un `UPDATE` sur une colonne qui
  devait être en lecture seule.

Le deuxième point est le pire. La perte était **silencieuse** : personne
n'obtenait d'erreur, seulement une colonne là où il attendait une expression.

## Ce que ce test fige

Le chemin complet, du contrat au SQL engendré, et les combinaisons refusées. Les
règles existaient déjà sur le format interne ; ce qui manquait était qu'un
contrat canonique les atteigne.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")
pytest.importorskip("jsonschema")

from forge_mvc_entities.canonical_model_normalizer import (  # noqa: E402
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.entity_semantic_validate import validate_semantic  # noqa: E402
from forge_mvc_entities.entity_validation_errors import (  # noqa: E402
    ALL_CODES,
    FORGE_ENTITY_INVALID_COMPUTED,
)


def _valideur() -> Any:
    import cli.schemas
    import referencing
    import referencing.jsonschema
    from jsonschema import Draft202012Validator

    dossier = Path(cli.schemas.__file__).parent
    registre = referencing.Registry()
    for fichier in dossier.glob("*.schema.json"):
        schema = json.loads(fichier.read_text(encoding="utf-8"))
        ressource = referencing.jsonschema.DRAFT202012.create_resource(schema)
        for cle in (schema.get("$id", fichier.name), fichier.name):
            registre = registre.with_resource(cle, ressource)
    return Draft202012Validator(
        json.loads((dossier / "entity.schema.json").read_text(encoding="utf-8")),
        registry=registre,
    )


CHAMP_CALCULE = {
    "name": "total", "type": "integer", "required": False,
    "nullable": True, "unique": False, "computed": "qte * pu",
}


def _entite(champ: "dict[str, Any] | None" = None) -> "dict[str, Any]":
    return {
        "schema_version": "1.0", "name": "Ligne", "table": "lignes",
        "fields": [
            {"name": "qte", "type": "integer", "required": True,
             "nullable": False, "unique": False},
            {"name": "pu", "type": "integer", "required": True,
             "nullable": False, "unique": False},
            dict(CHAMP_CALCULE) if champ is None else champ,
        ],
    }


def _avec(**modifs: Any) -> "dict[str, Any]":
    champ = dict(CHAMP_CALCULE)
    champ.update(modifs)
    return _entite(champ)


# ─────────────────────────────────────────────────────────────────────────────
# Le contrat accepte la clé
# ─────────────────────────────────────────────────────────────────────────────


class TestContrat:

    def test_le_schema_declare_computed(self) -> None:
        """`additionalProperties: false` refusait toute clé non déclarée."""
        import cli.schemas

        schema = json.loads(
            (Path(cli.schemas.__file__).parent / "field.schema.json")
            .read_text(encoding="utf-8"))

        assert "computed" in schema["properties"]
        assert schema["additionalProperties"] is False, (
            "le refus des clés inconnues doit rester : c'est lui qui a fait "
            "apparaître le défaut")

    def test_un_contrat_a_champ_calcule_passe_le_schema(self) -> None:
        assert list(_valideur().iter_errors(_entite())) == []

    @pytest.mark.parametrize("expression", ["", "   ", "\t\n"])
    def test_une_expression_sans_contenu_est_refusee(self, expression: str) -> None:
        """`minLength: 1` laissait passer trois espaces, qui auraient produit
        `(   ) AS "Total"`, du SQL invalide au premier `SELECT`."""
        assert list(_valideur().iter_errors(_avec(computed=expression))), (
            f"{expression!r} doit être refusée")

    def test_un_point_virgule_est_refuse(self) -> None:
        """L'expression est projetée dans un `SELECT`, pas exécutée."""
        assert list(_valideur().iter_errors(
            _avec(computed="qte * pu; DROP TABLE lignes")))


# ─────────────────────────────────────────────────────────────────────────────
# L'expression survit à la normalisation
# ─────────────────────────────────────────────────────────────────────────────


class TestPropagation:

    def _champs(self, entite: "dict[str, Any]") -> "dict[str, Any]":
        v1 = normalize_canonical_entity_for_model_build(entite)
        return {champ["name"]: champ for champ in v1["fields"]}

    def test_l_expression_atteint_la_representation_interne(self) -> None:
        """Le maillon qui manquait, et dont la rupture était muette."""
        assert self._champs(_entite())["total"]["computed"] == "qte * pu"

    def test_un_champ_ordinaire_n_en_porte_pas(self) -> None:
        assert "computed" not in self._champs(_entite())["qte"]

    def test_le_champ_garde_son_type_et_sa_colonne(self) -> None:
        """L'expression s'ajoute, elle ne remplace rien."""
        total = self._champs(_entite())["total"]

        assert total["forge_type"] == "integer"
        assert total["column"] == "Total"


# ─────────────────────────────────────────────────────────────────────────────
# Le SQL engendré
# ─────────────────────────────────────────────────────────────────────────────


class TestModeleEngendre:

    def _modele(self) -> str:
        from forge_mvc_entities.crud.model_builder import build_model

        return build_model(normalize_canonical_entity_for_model_build(_entite()))

    def _ligne(self, marqueur: str) -> str:
        return next(l for l in self._modele().splitlines() if marqueur in l)

    def test_le_select_projette_l_expression(self) -> None:
        assert '(qte * pu) AS \\"Total\\"' in self._ligne("SELECT_BY_ID")

    def test_l_insert_ignore_le_champ_calcule(self) -> None:
        """Sans quoi la base refuserait l'écriture d'une colonne inexistante."""
        assert "Total" not in self._ligne("INSERT       =")

    def test_l_update_ignore_le_champ_calcule(self) -> None:
        assert "Total" not in self._ligne("UPDATE       =")

    def test_les_champs_ordinaires_restent_ecrits(self) -> None:
        insert = self._ligne("INSERT       =")

        assert "Qte" in insert and "Pu" in insert


# ─────────────────────────────────────────────────────────────────────────────
# Les combinaisons impossibles
# ─────────────────────────────────────────────────────────────────────────────


class TestCombinaisonsRefusees:
    """Chacune produirait du SQL faux, pas une simple maladresse."""

    def _refus(self, entite: "dict[str, Any]") -> "list[Any]":
        if list(_valideur().iter_errors(entite)):
            return ["refus du schéma"]
        return validate_semantic([("ligne.json", entite)], [])

    @pytest.mark.parametrize(
        "cle,modif",
        [
            ("required", {"required": True}),
            ("unique", {"unique": True}),
            ("default", {"default": 0}),
            ("form", {"form": {"widget": "hidden"}}),
            ("source", {"source": "qte"}),
            ("foreign_key", {"type": "foreign_key", "references": "Autre"}),
        ],
    )
    def test_la_combinaison_est_refusee(self, cle: str, modif: "dict[str, Any]") -> None:
        assert self._refus(_avec(**modif)), (
            f"un champ calculé qui déclare aussi {cle} doit être refusé")

    def test_le_contrat_correct_passe(self) -> None:
        """Un relevé qui refuse tout ne garde rien."""
        assert self._refus(_entite()) == []

    def test_le_refus_porte_son_code(self) -> None:
        erreurs = validate_semantic([("ligne.json", _avec(unique=True))], [])

        assert erreurs
        assert erreurs[0].code == FORGE_ENTITY_INVALID_COMPUTED

    def test_le_refus_designe_le_champ_et_le_chemin(self) -> None:
        """Un message sans chemin fait chercher dans tout le contrat."""
        erreur = validate_semantic([("ligne.json", _avec(unique=True))], [])[0]

        assert "total" in erreur.message
        assert erreur.path == "$.fields[2].computed"

    def test_le_refus_dit_quoi_faire(self) -> None:
        erreur = validate_semantic([("ligne.json", _avec(unique=True))], [])[0]

        assert erreur.hint

    def test_le_code_figure_dans_la_liste_exhaustive(self) -> None:
        """`ALL_CODES` sert aux tests et à la documentation : un code absent
        s'y ferait oublier."""
        assert FORGE_ENTITY_INVALID_COMPUTED in ALL_CODES
