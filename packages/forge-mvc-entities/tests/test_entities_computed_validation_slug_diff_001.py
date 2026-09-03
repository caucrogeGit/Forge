"""Les quatre tickets `entities` du cycle rc8.

`ENTITIES-COMPUTED-FIELDS-001`, `ENTITIES-BUSINESS-VALIDATION-001`,
`ENTITIES-SLUG-ROUTES-001` et `ENTITIES-MIGRATION-DIFF-READABLE-001`.

Le contrat décrit des **types**. Il ne dit rien d'une valeur dérivée, ni d'une
règle métier, et la recherche par slug qu'il permet depuis l'ADR-017 n'avait
aucune route pour s'en servir.
"""
from __future__ import annotations

import ast
import copy
from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.crud.model_builder import build_model  # noqa: E402
from forge_mvc_entities.crud.routes_slug import (  # noqa: E402
    RESERVED_SLUG_SEGMENTS,
    slug_field_of,
    slug_route_lines,
)
from forge_mvc_entities.make_crud import build_routes_file  # noqa: E402
from forge_mvc_entities.migrations import (  # noqa: E402
    DIFF_DRIFT_STATUSES,
    SchemaDiffReport,
    SchemaDiffRow,
    has_schema_drift,
    summarize_schema_diff,
)
from forge_mvc_entities.validation import (  # noqa: E402
    EntityDefinitionError,
    validate_entity_definition,
)
from forge_mvc_entities.validators import (  # noqa: E402
    EntityValidationError,
    ValidationIssue,
    clear_entity_validators,
    ensure_entity_data,
    register_entity_validator,
    registered_validators,
    unregister_entity_validator,
    validate_entity_data,
)

_BASE: "dict[str, Any]" = {
    "format_version": 1,
    "entity": "Ligne",
    "table": "lignes",
    "fields": [
        {"name": "id", "column": "id", "sql_type": "INTEGER", "python_type": "int",
         "primary_key": True, "auto_increment": True, "nullable": False},
        {"name": "qte", "column": "qte", "sql_type": "INTEGER", "python_type": "int",
         "nullable": False},
        {"name": "pu", "column": "pu", "sql_type": "INTEGER", "python_type": "int",
         "nullable": False},
        {"name": "total", "column": "total", "sql_type": "INTEGER",
         "python_type": "int", "nullable": True, "computed": "qte * pu"},
    ],
}


def _contrat(**modifs: Any) -> "dict[str, Any]":
    contrat = copy.deepcopy(_BASE)
    contrat["fields"][3].update(modifs)
    return contrat


# ------------------------------------------------- ENTITIES-COMPUTED-FIELDS


class TestChampCalcule:

    def test_le_contrat_l_accepte(self) -> None:
        assert validate_entity_definition(_BASE)["fields"][3]["computed"] == "qte * pu"

    def test_l_expression_est_propagee_aux_generateurs(self) -> None:
        """La valider sans la propager laisserait le champ passer pour une
        colonne ordinaire."""
        normalise = validate_entity_definition(_BASE)

        assert "computed" in normalise["fields"][3]

    def test_il_est_projete_par_son_expression(self) -> None:
        """Il n'a pas de colonne : projeter son nom ferait échouer la requête."""
        modele = build_model(validate_entity_definition(_BASE))
        select = next(l for l in modele.splitlines() if "SELECT_BY_ID" in l)

        assert '(qte * pu) AS \\"total\\"' in select

    def test_l_expression_n_est_pas_prefixee_par_la_table(self) -> None:
        modele = build_model(validate_entity_definition(_BASE))
        select = next(l for l in modele.splitlines() if "SELECT_BY_ID" in l)

        assert "lignes.qte * pu" not in select

    def test_l_alias_reste_entre_guillemets(self) -> None:
        """C'est lui qui préserve la casse sur PostgreSQL, et le perdre
        rendrait la clé en minuscules."""
        modele = build_model(validate_entity_definition(_BASE))
        select = next(l for l in modele.splitlines() if "SELECT_BY_ID" in l)

        assert 'AS \\"total\\"' in select

    def test_il_est_absent_de_l_insert(self) -> None:
        """L'inclure ferait échouer la requête sur les quatre backends."""
        modele = build_model(validate_entity_definition(_BASE))
        insert = next(l for l in modele.splitlines() if l.startswith("INSERT"))

        assert "total" not in insert

    def test_il_est_absent_de_l_update(self) -> None:
        modele = build_model(validate_entity_definition(_BASE))
        update = next(l for l in modele.splitlines() if l.startswith("UPDATE"))

        assert "total" not in update

    def test_le_modele_engendre_compile(self) -> None:
        ast.parse(build_model(validate_entity_definition(_BASE)))


class TestChampCalculeRefuse:

    @pytest.mark.parametrize(
        "modif,motif",
        [
            ({"primary_key": True}, "clé primaire"),
            ({"unique": True}, "UNIQUE"),
            ({"default": 0}, "valeur par défaut"),
            ({"form": {"field": "string"}}, "formulaire"),
        ],
    )
    def test_les_combinaisons_impossibles_sont_refusees(
        self, modif: "dict[str, Any]", motif: str
    ) -> None:
        """Chacune produirait un SQL faux plutôt qu'une simple maladresse."""
        with pytest.raises(EntityDefinitionError):
            validate_entity_definition(_contrat(**modif))

    def test_un_point_virgule_est_refuse(self) -> None:
        """L'expression est projetée dans un SELECT, pas exécutée comme une
        instruction."""
        with pytest.raises(EntityDefinitionError):
            validate_entity_definition(_contrat(computed="qte; DROP TABLE x"))

    @pytest.mark.parametrize("vide", ["", "   ", 42, None])
    def test_une_expression_vide_est_refusee(self, vide: Any) -> None:
        if vide is None:
            pytest.skip("`None` vaut absence de champ calculé")
        with pytest.raises(EntityDefinitionError):
            validate_entity_definition(_contrat(computed=vide))


# ---------------------------------------------- ENTITIES-BUSINESS-VALIDATION


@pytest.fixture(autouse=True)
def _sans_validateur():
    clear_entity_validators()
    yield
    clear_entity_validators()


def _dates(donnees: "dict[str, Any]", ctx: "dict[str, Any]") -> "list[ValidationIssue]":
    if donnees.get("fin") and donnees.get("debut") and donnees["fin"] < donnees["debut"]:
        return [ValidationIssue("la date de fin doit suivre la date de début")]
    return []


class TestValidationMetier:

    def test_sans_regle_tout_passe(self) -> None:
        assert validate_entity_data("Contrat", {}).ok

    def test_une_regle_refuse(self) -> None:
        register_entity_validator("Contrat", _dates)

        assert not validate_entity_data("Contrat", {"debut": 5, "fin": 2}).ok

    def test_toutes_les_regles_sont_evaluees(self) -> None:
        """Rendre le premier problème seul obligerait l'utilisateur à corriger
        son formulaire une erreur à la fois."""
        register_entity_validator("Contrat", _dates)
        register_entity_validator(
            "Contrat", lambda d, c: "remise trop forte" if d.get("remise", 0) > 30 else None
        )

        rapport = validate_entity_data("Contrat", {"debut": 5, "fin": 2, "remise": 50})

        assert len(rapport.issues) == 2

    def test_une_chaine_seule_vaut_probleme(self) -> None:
        register_entity_validator("X", lambda d, c: "non")

        assert not validate_entity_data("X", {}).ok

    def test_un_probleme_sans_champ_est_permis(self) -> None:
        """« la date de fin doit suivre la date de début » n'appartient à aucun
        des deux, et la rattacher arbitrairement ferait pointer le formulaire
        au mauvais endroit."""
        register_entity_validator("Contrat", _dates)

        assert None in validate_entity_data("Contrat", {"debut": 5, "fin": 2}).by_field()

    def test_les_problemes_se_groupent_par_champ(self) -> None:
        register_entity_validator(
            "X", lambda d, c: [ValidationIssue("trop court", field="nom")]
        )

        assert validate_entity_data("X", {}).by_field()["nom"] == ["trop court"]

    def test_une_regle_qui_leve_produit_un_probleme(self) -> None:
        """Le jour où le service qu'elle interroge tombe, tout passerait."""
        def _panne(d: Any, c: Any) -> Any:
            raise ConnectionError("service HS")

        register_entity_validator("X", _panne)

        assert not validate_entity_data("X", {}).ok

    @pytest.mark.parametrize("verdict", [42, object(), {"a": 1}])
    def test_un_verdict_illisible_produit_un_probleme(self, verdict: Any) -> None:
        register_entity_validator("X", lambda d, c: verdict)

        assert not validate_entity_data("X", {}).ok

    def test_les_regles_sont_par_entite(self) -> None:
        register_entity_validator("Contrat", _dates)

        assert validate_entity_data("Facture", {"debut": 5, "fin": 2}).ok

    def test_un_double_enregistrement_ne_double_pas(self) -> None:
        register_entity_validator("X", _dates)
        register_entity_validator("X", _dates)

        assert len(registered_validators("X")) == 1

    def test_on_peut_debrancher(self) -> None:
        register_entity_validator("X", _dates)

        assert unregister_entity_validator("X", _dates) is True

    def test_ensure_leve_avec_le_rapport(self) -> None:
        """Un contrôleur doit pouvoir rendre chaque problème en face de son champ."""
        register_entity_validator("Contrat", _dates)

        with pytest.raises(EntityValidationError) as leve:
            ensure_entity_data("Contrat", {"debut": 5, "fin": 2})

        assert leve.value.report.issues

    def test_une_regle_non_appelable_est_refusee(self) -> None:
        with pytest.raises(TypeError):
            register_entity_validator("X", "pas une fonction")  # type: ignore[arg-type]

    def test_aucune_mini_langue_dans_le_contrat(self) -> None:
        """Une mini-langue d'expressions demanderait un interpréteur, c'est à
        dire du code caché dans de la donnée."""
        from forge_mvc_entities.validation import ALLOWED_FIELD_KEYS

        assert "validate" not in ALLOWED_FIELD_KEYS
        assert "rule" not in ALLOWED_FIELD_KEYS


# ---------------------------------------------------- ENTITIES-SLUG-ROUTES


def _avec_slug() -> "dict[str, Any]":
    contrat = copy.deepcopy(_BASE)
    contrat["fields"].append({
        "name": "slug", "column": "slug", "sql_type": "TEXT",
        "python_type": "str", "nullable": False, "form": {"field": "slug"},
    })
    return contrat


class TestRoutePublique:

    def test_sans_slug_aucune_route_publique(self) -> None:
        """La sortie reste celle d'avant pour une entité sans slug."""
        assert slug_route_lines(_BASE, "ligne", "LigneController") == []
        assert "show_by_slug" not in build_routes_file(_BASE)

    def test_avec_slug_la_route_est_posee(self) -> None:
        rendu = build_routes_file(_avec_slug())

        assert "show_by_slug" in rendu
        assert '"/{slug}"' in rendu

    def test_elle_est_publique(self) -> None:
        """Une fiche adressée par slug est faite pour être lue sans compte."""
        rendu = build_routes_file(_avec_slug())

        assert "public=True" in rendu

    def test_elle_vient_en_dernier(self) -> None:
        """Un slug valant « new » serait sinon capturé par le segment fixe."""
        rendu = build_routes_file(_avec_slug())

        assert rendu.index("export-csv") < rendu.index("show_by_slug")

    def test_les_segments_reserves_sont_nommes(self) -> None:
        """C'est à l'application de les écarter à l'écriture, et cette liste
        est là pour qu'elle sache lesquels."""
        assert "new" in RESERVED_SLUG_SEGMENTS
        assert "export-csv" in RESERVED_SLUG_SEGMENTS

    def test_le_champ_slug_est_reconnu(self) -> None:
        assert slug_field_of(_avec_slug()) == "slug"
        assert slug_field_of(_BASE) == ""

    def test_le_controleur_gagne_la_methode(self) -> None:
        from forge_mvc_entities.crud.controller_builder import build_controller

        source = build_controller(validate_entity_definition(_avec_slug()))

        assert "def show_by_slug" in source
        ast.parse(source)

    def test_la_methode_refuse_un_slug_vide(self) -> None:
        from forge_mvc_entities.crud.controller_builder import build_controller

        source = build_controller(validate_entity_definition(_avec_slug()))
        bloc = source[source.index("def show_by_slug"):]

        assert "if not slug" in bloc
        assert "not_found" in bloc


# ------------------------------------------ ENTITIES-MIGRATION-DIFF-READABLE


def _rapport(*statuts: str, table: str = "OK") -> SchemaDiffReport:
    return SchemaDiffReport(
        entity="Ligne", table="lignes", table_status=table,
        rows=[SchemaDiffRow(s, f"col{i}", "") for i, s in enumerate(statuts)],
    )


class TestResumeDeDiff:

    def test_il_compte_par_statut(self) -> None:
        """Sur une entité de trente colonnes, savoir s'il reste un écart
        demandait de lire trente lignes et de compter à la main."""
        resume = summarize_schema_diff(_rapport("OK", "OK", "COLUMN_MISSING"))

        assert resume == {"OK": 2, "COLUMN_MISSING": 1}

    def test_un_rapport_sans_ecart_le_dit(self) -> None:
        assert not has_schema_drift(_rapport("OK", "OK"))

    @pytest.mark.parametrize("statut", sorted(DIFF_DRIFT_STATUSES))
    def test_chaque_statut_d_ecart_compte(self, statut: str) -> None:
        assert has_schema_drift(_rapport("OK", statut))

    def test_une_table_absente_est_le_plus_grand_ecart(self) -> None:
        assert has_schema_drift(_rapport(table="TABLE_MISSING"))

    def test_un_rapport_vide_et_conforme_n_a_pas_d_ecart(self) -> None:
        assert not has_schema_drift(_rapport())
