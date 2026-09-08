"""`WORKFLOW-NORMALISATION-FRONTIERE-001` — une condition ne dépend pas de la casse.

`can_transition` normalisait les noms pour vérifier la transition, mais les
valeurs brutes continuaient leur route. Une condition enregistrée pour
`draft -> done` n'était donc pas retrouvée quand l'appelant écrivait
`DRAFT -> DONE` : la transition était jugée valide, la condition introuvable, et
`commit` était appelé.

Mesuré, sur des modules inchangés :

    apply_transition(rules, 'draft', 'done')  -> refusé par la condition
    apply_transition(rules, 'DRAFT', 'DONE')  -> commit appelé avec 'DONE'

Une précondition métier qui dépend de la casse de son appelant n'est pas une
précondition. Le remède est de normaliser **une fois à la frontière**, et de se
servir de cette forme partout : conditions, événement, écriture, valeur rendue.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow.conditions import clear_conditions, register_condition  # noqa: E402
from forge_mvc_workflow.hooks import apply_transition  # noqa: E402
from forge_mvc_workflow.transitions import (  # noqa: E402
    WorkflowTransitionError,
    make_transition,
)


@pytest.fixture(autouse=True)
def registre_propre():
    """Le registre de conditions est global : le rendre après chaque test."""
    clear_conditions()
    yield
    clear_conditions()


@pytest.fixture
def regles():
    return [make_transition("draft", "done")]


class TestUneConditionRefusanteRefuseToutesLesFormes:
    """Le cœur du défaut : la casse ne doit ouvrir aucune porte."""

    @pytest.mark.parametrize(
        ("depart", "arrivee"),
        [
            ("draft", "done"),
            ("DRAFT", "DONE"),
            ("Draft", "Done"),
            ("  draft  ", "  done  "),
            ("draft", "DONE"),
        ],
        ids=["canonique", "majuscules", "capitalise", "espaces", "mixte"],
    )
    def test_toutes_les_variantes_sont_refusees(self, depart, arrivee, regles) -> None:
        register_condition(
            lambda *_: "relecture manquante", from_status="draft", to_status="done"
        )
        ecrits: list[str] = []

        with pytest.raises(WorkflowTransitionError, match="relecture manquante"):
            apply_transition(
                regles, depart, arrivee, commit=lambda e: ecrits.append(e.to_status)
            )

        assert ecrits == [], "aucune écriture ne doit avoir lieu sur un refus"


class TestLaFormeCanoniqueCirculePartout:
    """Ce qui est rendu et écrit est le statut canonique, jamais la saisie."""

    def test_l_evenement_porte_la_forme_canonique(self, regles) -> None:
        vus: list[tuple[str, str]] = []

        apply_transition(
            regles, "DRAFT", "DONE",
            commit=lambda e: vus.append((e.from_status, e.to_status)),
        )

        assert vus == [("draft", "done")]

    def test_la_valeur_rendue_est_canonique(self, regles) -> None:
        """Elle rendait `DONE`, que l'application écrivait ensuite en base."""
        assert apply_transition(regles, "DRAFT", "DONE") == "done"

    def test_les_trois_points_d_accroche_voient_la_meme_forme(self, regles) -> None:
        vus: list[str] = []

        apply_transition(
            regles, "DRAFT", "DONE",
            before=lambda e: vus.append(f"before:{e.to_status}"),
            commit=lambda e: vus.append(f"commit:{e.to_status}"),
            after=lambda e: vus.append(f"after:{e.to_status}"),
        )

        assert vus == ["before:done", "commit:done", "after:done"]


class TestCeQuiNeDoitPasChanger:
    """La normalisation ne rend pas valide ce qui ne l'était pas."""

    def test_une_transition_non_declaree_reste_refusee(self, regles) -> None:
        with pytest.raises(WorkflowTransitionError, match="non déclarée"):
            apply_transition(regles, "DONE", "DRAFT")

    def test_une_condition_qui_accepte_laisse_passer(self, regles) -> None:
        register_condition(lambda *_: None, from_status="draft", to_status="done")
        ecrits: list[str] = []

        resultat = apply_transition(
            regles, "DRAFT", "DONE", commit=lambda e: ecrits.append(e.to_status)
        )

        assert resultat == "done"
        assert ecrits == ["done"]

    def test_une_condition_generale_s_applique_aussi(self, regles) -> None:
        """Sans `from_status` ni `to_status`, elle vaut pour toutes les transitions."""
        register_condition(lambda *_: "gel des écritures")

        with pytest.raises(WorkflowTransitionError, match="gel des écritures"):
            apply_transition(regles, "DRAFT", "DONE")
