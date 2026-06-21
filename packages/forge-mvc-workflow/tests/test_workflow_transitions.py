from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (
    WorkflowTransition,
    WorkflowTransitionError,
    can_transition,
    get_available_transitions,
    make_status,
    make_transition,
    validate_statuses,
    validate_transitions,
)


# ---------------------------------------------------------------------------
# Fixtures communes
# ---------------------------------------------------------------------------

STATUTS = validate_statuses([
    make_status("draft", is_initial=True),
    make_status("pending"),
    make_status("published", is_final=True),
    make_status("archived", is_final=True),
])

TRANSITIONS = validate_transitions(
    [
        make_transition("draft", "pending"),
        make_transition("pending", "published"),
        make_transition("pending", "draft"),
        make_transition("published", "archived"),
    ],
    statuses=STATUTS,
)


# ---------------------------------------------------------------------------
# WorkflowTransition — création et validation basique
# ---------------------------------------------------------------------------


def test_creation_transition_valide():
    t = WorkflowTransition(from_status="draft", to_status="pending")
    assert t.from_status == "draft"
    assert t.to_status == "pending"


def test_make_transition_fabrique_transition_valide():
    t = make_transition("pending", "published")
    assert t.from_status == "pending"
    assert t.to_status == "published"


def test_transition_normalise_les_noms():
    t = make_transition("In-Progress", "Done")
    assert t.from_status == "in_progress"
    assert t.to_status == "done"


def test_transition_refuse_nom_source_vide():
    with pytest.raises(WorkflowTransitionError):
        make_transition("", "pending")


def test_transition_refuse_nom_cible_vide():
    with pytest.raises(WorkflowTransitionError):
        make_transition("draft", "")


def test_transition_refuse_nom_source_dangereux():
    with pytest.raises(WorkflowTransitionError):
        make_transition("bad/name", "pending")


def test_transition_refuse_nom_cible_dangereux():
    with pytest.raises(WorkflowTransitionError):
        make_transition("draft", "bad.name")


def test_transition_refuse_source_egale_cible():
    with pytest.raises(WorkflowTransitionError, match="même statut"):
        make_transition("draft", "draft")


def test_transition_est_immuable():
    t = make_transition("draft", "pending")
    with pytest.raises(Exception):
        t.from_status = "other"


# ---------------------------------------------------------------------------
# validate_transitions — cohérence de la liste
# ---------------------------------------------------------------------------


def test_validate_transitions_liste_valide():
    transitions = [
        make_transition("draft", "pending"),
        make_transition("pending", "published"),
    ]
    result = validate_transitions(transitions)
    assert result is transitions


def test_validate_transitions_refuse_doublons():
    transitions = [
        make_transition("draft", "pending"),
        make_transition("draft", "pending"),
    ]
    with pytest.raises(WorkflowTransitionError, match="doublon"):
        validate_transitions(transitions)


def test_validate_transitions_accepte_liste_vide():
    assert validate_transitions([]) == []


def test_validate_transitions_verifie_statuts_connus():
    statuses = [make_status("draft"), make_status("pending")]
    transitions = [make_transition("draft", "pending")]
    result = validate_transitions(transitions, statuses=statuses)
    assert len(result) == 1


def test_validate_transitions_refuse_statut_source_inconnu():
    statuses = [make_status("draft"), make_status("pending")]
    transitions = [make_transition("unknown", "pending")]
    with pytest.raises(WorkflowTransitionError, match="source inconnu"):
        validate_transitions(transitions, statuses=statuses)


def test_validate_transitions_refuse_statut_cible_inconnu():
    statuses = [make_status("draft"), make_status("pending")]
    transitions = [make_transition("draft", "nowhere")]
    with pytest.raises(WorkflowTransitionError, match="cible inconnu"):
        validate_transitions(transitions, statuses=statuses)


def test_validate_transitions_sans_statuts_ne_verifie_pas_existence():
    transitions = [make_transition("foo", "bar")]
    result = validate_transitions(transitions)
    assert len(result) == 1


def test_validate_transitions_plusieurs_cibles_depuis_meme_source():
    transitions = [
        make_transition("pending", "published"),
        make_transition("pending", "draft"),
    ]
    result = validate_transitions(transitions)
    assert len(result) == 2


def test_validate_transitions_plusieurs_sources_vers_meme_cible():
    transitions = [
        make_transition("draft", "published"),
        make_transition("pending", "published"),
    ]
    result = validate_transitions(transitions)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# can_transition
# ---------------------------------------------------------------------------


def test_can_transition_retourne_true_si_autorisee():
    assert can_transition(TRANSITIONS, "draft", "pending") is True


def test_can_transition_retourne_false_si_non_autorisee():
    assert can_transition(TRANSITIONS, "draft", "published") is False


def test_can_transition_retourne_false_si_liste_vide():
    assert can_transition([], "draft", "pending") is False


def test_can_transition_normalise_les_noms():
    assert can_transition(TRANSITIONS, "Draft", "Pending") is True


def test_can_transition_statut_final_vers_autre_si_non_declare():
    assert can_transition(TRANSITIONS, "published", "draft") is False


def test_can_transition_statut_final_vers_archive_si_declare():
    assert can_transition(TRANSITIONS, "published", "archived") is True


# ---------------------------------------------------------------------------
# get_available_transitions
# ---------------------------------------------------------------------------


def test_get_available_transitions_retourne_cibles_possibles():
    result = get_available_transitions(TRANSITIONS, "pending")
    names = {t.to_status for t in result}
    assert names == {"published", "draft"}


def test_get_available_transitions_retourne_liste_vide_si_aucune():
    result = get_available_transitions(TRANSITIONS, "archived")
    assert result == []


def test_get_available_transitions_normalise_le_nom():
    result = get_available_transitions(TRANSITIONS, "Draft")
    assert len(result) == 1
    assert result[0].to_status == "pending"


def test_get_available_transitions_liste_vide():
    assert get_available_transitions([], "draft") == []


# ---------------------------------------------------------------------------
# API publique importable depuis core.workflow
# ---------------------------------------------------------------------------


def test_api_transitions_importable():
    from forge_mvc_workflow import (
        WorkflowTransition,
        WorkflowTransitionError,
        can_transition,
        get_available_transitions,
        make_transition,
        validate_transitions,
    )
    assert WorkflowTransition is not None
    assert WorkflowTransitionError is not None
    assert callable(make_transition)
    assert callable(validate_transitions)
    assert callable(can_transition)
    assert callable(get_available_transitions)


# ---------------------------------------------------------------------------
# Aucun accès base de données ni fichier applicatif
# ---------------------------------------------------------------------------


def test_transitions_sans_acces_base_de_donnees():
    t = make_transition("new", "in_progress")
    assert t.from_status == "new"
    assert t.to_status == "in_progress"


def test_workflow_complet_generique():
    statuses = validate_statuses([
        make_status("new", is_initial=True),
        make_status("in_progress"),
        make_status("done", is_final=True),
        make_status("cancelled", is_final=True),
    ])
    transitions = validate_transitions(
        [
            make_transition("new", "in_progress"),
            make_transition("in_progress", "done"),
            make_transition("in_progress", "cancelled"),
            make_transition("new", "cancelled"),
        ],
        statuses=statuses,
    )
    assert can_transition(transitions, "new", "in_progress") is True
    assert can_transition(transitions, "done", "new") is False
    available = get_available_transitions(transitions, "in_progress")
    assert {t.to_status for t in available} == {"done", "cancelled"}
