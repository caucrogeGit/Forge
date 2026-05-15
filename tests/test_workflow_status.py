from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_workflow")

from forge_mvc_workflow import (
    WorkflowStatus,
    WorkflowStatusError,
    find_status,
    make_status,
    normalize_status_name,
    validate_status_name,
    validate_statuses,
)


# ---------------------------------------------------------------------------
# WorkflowStatus — création et valeurs par défaut
# ---------------------------------------------------------------------------


def test_creation_statut_valide():
    s = WorkflowStatus(name="pending", label="En attente", color="yellow")
    assert s.name == "pending"
    assert s.label == "En attente"
    assert s.color == "yellow"
    assert s.is_initial is False
    assert s.is_final is False


def test_creation_avec_make_status():
    s = make_status("published", label="Publié", color="green", is_final=True)
    assert s.name == "published"
    assert s.label == "Publié"
    assert s.is_final is True


def test_label_fallback_vers_name():
    s = WorkflowStatus(name="draft")
    assert s.label == "draft"


def test_label_fallback_via_make_status():
    s = make_status("archived")
    assert s.label == "archived"


def test_is_initial_et_is_final_false_par_defaut():
    s = WorkflowStatus(name="new")
    assert s.is_initial is False
    assert s.is_final is False


def test_statut_initial():
    s = WorkflowStatus(name="new", is_initial=True)
    assert s.is_initial is True


def test_statut_final():
    s = WorkflowStatus(name="done", is_final=True)
    assert s.is_final is True


def test_plusieurs_statuts_finaux_acceptes():
    statuses = [
        WorkflowStatus(name="done", is_final=True),
        WorkflowStatus(name="cancelled", is_final=True),
    ]
    result = validate_statuses(statuses)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# normalize_status_name
# ---------------------------------------------------------------------------


def test_normalisation_minuscules():
    assert normalize_status_name("Pending") == "pending"


def test_normalisation_espaces_vers_underscore():
    assert normalize_status_name("in progress") == "in_progress"


def test_normalisation_tirets_vers_underscore():
    assert normalize_status_name("in-progress") == "in_progress"


def test_normalisation_espaces_multiples():
    assert normalize_status_name("  en  attente  ") == "en_attente"


def test_normalisation_mixte():
    assert normalize_status_name("En-Cours") == "en_cours"


def test_normalisation_deja_valide():
    assert normalize_status_name("draft") == "draft"


# ---------------------------------------------------------------------------
# validate_status_name
# ---------------------------------------------------------------------------


def test_validation_nom_valide():
    assert validate_status_name("pending") == "pending"


def test_validation_normalise_le_nom():
    assert validate_status_name("in-progress") == "in_progress"


def test_validation_refuse_nom_vide():
    with pytest.raises(WorkflowStatusError):
        validate_status_name("")


def test_validation_refuse_espaces_seuls():
    with pytest.raises(WorkflowStatusError):
        validate_status_name("   ")


def test_validation_refuse_nom_dangereux_caracteres_speciaux():
    with pytest.raises(WorkflowStatusError):
        validate_status_name("bad/name")


def test_validation_refuse_commencant_par_chiffre():
    with pytest.raises(WorkflowStatusError):
        validate_status_name("1invalid")


def test_validation_refuse_nom_avec_point():
    with pytest.raises(WorkflowStatusError):
        validate_status_name("sta.tut")


def test_creation_statut_refuse_nom_vide():
    with pytest.raises(WorkflowStatusError):
        WorkflowStatus(name="")


def test_creation_statut_refuse_nom_dangereux():
    with pytest.raises(WorkflowStatusError):
        WorkflowStatus(name="bad/name")


# ---------------------------------------------------------------------------
# validate_statuses
# ---------------------------------------------------------------------------


def test_validation_liste_valide():
    statuses = [
        WorkflowStatus(name="draft", is_initial=True),
        WorkflowStatus(name="published"),
        WorkflowStatus(name="archived", is_final=True),
    ]
    result = validate_statuses(statuses)
    assert result is statuses


def test_validation_refuse_doublons():
    statuses = [
        WorkflowStatus(name="draft"),
        WorkflowStatus(name="draft"),
    ]
    with pytest.raises(WorkflowStatusError, match="doublon"):
        validate_statuses(statuses)


def test_validation_accepte_un_seul_statut_initial():
    statuses = [
        WorkflowStatus(name="new", is_initial=True),
        WorkflowStatus(name="done"),
    ]
    result = validate_statuses(statuses)
    assert len(result) == 2


def test_validation_refuse_plusieurs_statuts_initiaux():
    statuses = [
        WorkflowStatus(name="new", is_initial=True),
        WorkflowStatus(name="draft", is_initial=True),
    ]
    with pytest.raises(WorkflowStatusError, match="initial"):
        validate_statuses(statuses)


def test_validation_liste_vide_acceptee():
    assert validate_statuses([]) == []


# ---------------------------------------------------------------------------
# find_status
# ---------------------------------------------------------------------------


def test_find_status_retrouve_statut_existant():
    statuses = [
        WorkflowStatus(name="draft"),
        WorkflowStatus(name="published"),
        WorkflowStatus(name="archived"),
    ]
    result = find_status(statuses, "published")
    assert result is not None
    assert result.name == "published"


def test_find_status_retourne_none_si_absent():
    statuses = [WorkflowStatus(name="draft")]
    assert find_status(statuses, "unknown") is None


def test_find_status_liste_vide_retourne_none():
    assert find_status([], "draft") is None


# ---------------------------------------------------------------------------
# API publique importable depuis core.workflow
# ---------------------------------------------------------------------------


def test_api_publique_importable():
    from forge_mvc_workflow import (
        WorkflowStatus,
        WorkflowStatusError,
        find_status,
        make_status,
        normalize_status_name,
        validate_status_name,
        validate_statuses,
    )
    assert WorkflowStatus is not None
    assert WorkflowStatusError is not None
    assert callable(normalize_status_name)
    assert callable(validate_status_name)
    assert callable(make_status)
    assert callable(validate_statuses)
    assert callable(find_status)


# ---------------------------------------------------------------------------
# Aucun accès base de données ni fichier applicatif
# ---------------------------------------------------------------------------


def test_aucun_acces_base_de_donnees():
    s = make_status("pending")
    assert s.name == "pending"


def test_statuts_generiques_sans_metier_communes_sejours():
    statuses = [
        make_status("draft", is_initial=True),
        make_status("pending"),
        make_status("published"),
        make_status("archived", is_final=True),
    ]
    result = validate_statuses(statuses)
    assert len(result) == 4
    found = find_status(result, "pending")
    assert found is not None
    assert found.label == "pending"
