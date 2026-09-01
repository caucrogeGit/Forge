"""WORKFLOW-ENTITY-STATUS-001 : les statuts viennent du contrat d'entité.

Une application qui gère un cycle de vie déclarait sa liste de statuts deux
fois : en `choices` du contrat, pour le formulaire et la base, et en Python
pour le workflow.

Rien ne gardait les deux identiques. Ajouter un statut au contrat sans toucher
au workflow donne un choix que le formulaire propose et que la transition
refuse ; le retirer donne une transition vers un statut que la base n'accepte
plus. Dans les deux cas, la panne n'apparaît qu'à l'usage, sur un seul chemin.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (  # noqa: E402
    EntityStatusError,
    WorkflowTransitionError,
    make_transition,
    status_values,
    statuses_from_choices,
    statuses_from_entity_field,
    validate_transitions,
)

CHOIX = [
    {"value": "draft", "label": "Brouillon"},
    {"value": "published", "label": "Publié"},
    {"value": "archived", "label": "Archivé"},
]


def _contrat(**champ_statut: Any) -> dict[str, Any]:
    statut: dict[str, Any] = {"name": "statut", "type": "string", "choices": CHOIX}
    statut.update(champ_statut)
    return {
        "name": "Article",
        "fields": [{"name": "titre", "type": "string"}, statut],
    }


class TestLectureDuContrat:
    def test_les_statuts_viennent_des_choix(self) -> None:
        statuts = statuses_from_entity_field(_contrat(), "statut")
        assert status_values(statuts) == ["draft", "published", "archived"]

    def test_l_ordre_du_contrat_est_conserve(self) -> None:
        """C'est celui que le formulaire affiche : en changer ferait diverger deux vues."""
        inverse = list(reversed(CHOIX))
        statuts = statuses_from_choices(inverse)
        assert status_values(statuts) == ["archived", "published", "draft"]

    def test_le_libelle_du_contrat_est_repris(self) -> None:
        statuts = statuses_from_entity_field(_contrat(), "statut")
        assert statuts[0].label == "Brouillon"

    def test_un_choix_sans_libelle_reste_utilisable(self) -> None:
        """`WorkflowStatus` retombe sur le nom, comportement déjà en place."""
        statuts = statuses_from_choices([{"value": "draft"}])
        assert statuts[0].name == "draft"
        assert statuts[0].label == "draft"


class TestDebutEtFin:
    def test_l_initial_et_les_finaux_sont_declares(self) -> None:
        """Un contrat dit les valeurs permises, jamais laquelle commence."""
        statuts = statuses_from_entity_field(
            _contrat(), "statut", initial="draft", final=("archived",)
        )
        assert statuts[0].is_initial
        assert statuts[-1].is_final

    def test_sans_declaration_aucun_statut_n_est_initial(self) -> None:
        """Prendre le premier serait une règle inventée par Forge."""
        statuts = statuses_from_entity_field(_contrat(), "statut")
        assert not any(s.is_initial for s in statuts)

    def test_un_initial_absent_des_choix_est_refuse(self) -> None:
        """Une faute de frappe donnerait un cycle sans début, que rien ne signalerait."""
        with pytest.raises(EntityStatusError, match="initial"):
            statuses_from_entity_field(_contrat(), "statut", initial="brouillon")

    def test_un_final_absent_des_choix_est_refuse(self) -> None:
        with pytest.raises(EntityStatusError, match="final"):
            statuses_from_entity_field(_contrat(), "statut", final=("supprime",))


class TestContratInexploitable:
    def test_un_champ_absent_est_refuse_en_nommant_les_autres(self) -> None:
        with pytest.raises(EntityStatusError, match="titre"):
            statuses_from_entity_field(_contrat(), "etat")

    def test_un_champ_sans_choix_est_refuse(self) -> None:
        contrat = {"name": "A", "fields": [{"name": "statut", "type": "string"}]}
        with pytest.raises(EntityStatusError, match="choices"):
            statuses_from_entity_field(contrat, "statut")

    def test_un_contrat_sans_champ_est_refuse(self) -> None:
        with pytest.raises(EntityStatusError, match="aucun champ"):
            statuses_from_entity_field({"name": "A"}, "statut")

    @pytest.mark.parametrize(
        "choix",
        [[{"label": "x"}], [{"value": ""}], [{"value": "   "}], ["pas un objet"], "pas une liste"],
    )
    def test_un_choix_malforme_est_refuse(self, choix: Any) -> None:
        with pytest.raises(EntityStatusError):
            statuses_from_choices(choix)

    def test_un_doublon_est_refuse(self) -> None:
        """Deux fois la même valeur rendrait le cycle ambigu."""
        with pytest.raises(EntityStatusError, match="double"):
            statuses_from_choices([{"value": "draft"}, {"value": "draft"}])


class TestSourceUnique:
    """Le contrat devient la source, et l'écart se voit."""

    def test_une_transition_vers_un_statut_absent_du_contrat_est_refusee(self) -> None:
        """Le cas qui motivait le ticket : la base n'accepterait pas la valeur."""
        statuts = statuses_from_entity_field(_contrat(), "statut")
        transitions = [make_transition("draft", "supprime")]

        with pytest.raises(WorkflowTransitionError, match="supprime"):
            validate_transitions(transitions, statuts)

    def test_des_transitions_coherentes_passent(self) -> None:
        statuts = statuses_from_entity_field(_contrat(), "statut")
        transitions = [
            make_transition("draft", "published"),
            make_transition("published", "archived"),
        ]

        assert validate_transitions(transitions, statuts) == transitions

    def test_un_statut_ajoute_au_contrat_est_immediatement_connu(self) -> None:
        """Sans double déclaration, le workflow suit le contrat sans effort."""
        contrat = _contrat()
        contrat["fields"][1]["choices"] = [*CHOIX, {"value": "review", "label": "Relecture"}]

        statuts = statuses_from_entity_field(contrat, "statut")
        assert "review" in status_values(statuts)
        validate_transitions([make_transition("draft", "review")], statuts)


class TestSansDependance:
    def test_workflow_n_importe_pas_le_moteur_d_entites(self) -> None:
        """Un contrat est un dictionnaire JSON : le lire ne demande aucun paquet."""
        from forge_mvc_workflow import entities

        arbre = ast.parse(Path(entities.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        assert not any(m.startswith("forge_mvc_entities") for m in modules)

    def test_le_champ_est_nomme_jamais_devine(self) -> None:
        """Repérer « le champ qui ressemble à un statut » se tromperait sur deux."""
        contrat = {
            "name": "A",
            "fields": [
                {"name": "statut", "type": "string", "choices": CHOIX},
                {"name": "etat_paiement", "type": "string", "choices": [{"value": "du"}]},
            ],
        }
        assert status_values(statuses_from_entity_field(contrat, "etat_paiement")) == ["du"]
