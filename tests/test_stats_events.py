from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats import (
    StatsEvent,
    StatsEventError,
    make_event,
    normalize_event_name,
    validate_event,
    validate_event_name,
)


# ---------------------------------------------------------------------------
# StatsEvent — création et valeurs par défaut
# ---------------------------------------------------------------------------


def test_creation_evenement_valide():
    e = StatsEvent(name="page_view", label="Vue de page", category="traffic")
    assert e.name == "page_view"
    assert e.label == "Vue de page"
    assert e.category == "traffic"
    assert e.metadata == {}


def test_creation_avec_make_event():
    e = make_event("contact_click", label="Clic contact", category="engagement")
    assert e.name == "contact_click"
    assert e.label == "Clic contact"
    assert e.category == "engagement"


def test_label_fallback_vers_name():
    e = StatsEvent(name="page_view")
    assert e.label == "page_view"


def test_label_fallback_via_make_event():
    e = make_event("form_submit")
    assert e.label == "form_submit"


def test_category_defaut_general():
    e = StatsEvent(name="page_view")
    assert e.category == "general"


def test_category_defaut_via_make_event():
    e = make_event("page_view")
    assert e.category == "general"


def test_metadata_vide_par_defaut():
    e = StatsEvent(name="page_view")
    assert e.metadata == {}


def test_metadata_personnalisee_acceptee():
    e = make_event("page_view", metadata={"path": "/contact", "referrer": "google"})
    assert e.metadata["path"] == "/contact"
    assert e.metadata["referrer"] == "google"


def test_metadata_none_remplace_par_dict_vide():
    e = make_event("page_view", metadata=None)
    assert e.metadata == {}


def test_evenement_est_immutable():
    e = make_event("page_view")
    with pytest.raises(Exception):
        e.name = "other"


# ---------------------------------------------------------------------------
# normalize_event_name
# ---------------------------------------------------------------------------


def test_normalisation_minuscules():
    assert normalize_event_name("PageView") == "pageview"


def test_normalisation_espaces_vers_underscore():
    assert normalize_event_name("page view") == "page_view"


def test_normalisation_tirets_vers_underscore():
    assert normalize_event_name("page-view") == "page_view"


def test_normalisation_deja_valide():
    assert normalize_event_name("page_view") == "page_view"


def test_normalisation_espaces_multiples():
    assert normalize_event_name("  contact  click  ") == "contact_click"


def test_normalisation_mixte():
    assert normalize_event_name("External-Link Click") == "external_link_click"


# ---------------------------------------------------------------------------
# validate_event_name
# ---------------------------------------------------------------------------


def test_validation_nom_valide():
    assert validate_event_name("page_view") == "page_view"


def test_validation_normalise_avant_validation():
    assert validate_event_name("page-view") == "page_view"


def test_validation_refuse_nom_vide():
    with pytest.raises(StatsEventError):
        validate_event_name("")


def test_validation_refuse_espaces_seuls():
    with pytest.raises(StatsEventError):
        validate_event_name("   ")


def test_validation_refuse_nom_commencant_par_chiffre():
    with pytest.raises(StatsEventError):
        validate_event_name("1_event")


def test_validation_refuse_chemin():
    with pytest.raises(StatsEventError):
        validate_event_name("../../admin")


def test_validation_refuse_url():
    with pytest.raises(StatsEventError):
        validate_event_name("http://site.com")


def test_validation_refuse_html():
    with pytest.raises(StatsEventError):
        validate_event_name("<script>")


def test_validation_refuse_slash():
    with pytest.raises(StatsEventError):
        validate_event_name("page/view")


def test_creation_statut_refuse_nom_vide():
    with pytest.raises(StatsEventError):
        StatsEvent(name="")


def test_creation_statut_refuse_nom_dangereux():
    with pytest.raises(StatsEventError):
        StatsEvent(name="<script>alert(1)</script>")


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


def test_metadata_refuse_liste():
    with pytest.raises(StatsEventError):
        StatsEvent(name="page_view", metadata=["a", "b"])


def test_metadata_refuse_chaine():
    with pytest.raises(StatsEventError):
        StatsEvent(name="page_view", metadata="mauvais")


def test_metadata_refuse_entier():
    with pytest.raises(StatsEventError):
        StatsEvent(name="page_view", metadata=42)


def test_metadata_accepte_dict_avec_valeurs_variees():
    e = make_event("media_view", metadata={"id": 1, "type": "image", "flag": True})
    assert e.metadata["id"] == 1
    assert e.metadata["type"] == "image"
    assert e.metadata["flag"] is True


# ---------------------------------------------------------------------------
# validate_event
# ---------------------------------------------------------------------------


def test_validate_event_retourne_l_evenement():
    e = make_event("page_view")
    result = validate_event(e)
    assert result is e


def test_validate_event_refuse_non_stats_event():
    with pytest.raises(StatsEventError):
        validate_event({"name": "page_view"})


def test_validate_event_refuse_none():
    with pytest.raises(StatsEventError):
        validate_event(None)


def test_validate_event_refuse_chaine():
    with pytest.raises(StatsEventError):
        validate_event("page_view")


# ---------------------------------------------------------------------------
# API publique importable depuis core.stats
# ---------------------------------------------------------------------------


def test_api_publique_importable():
    from forge_mvc_stats import (
        StatsEvent,
        StatsEventError,
        make_event,
        normalize_event_name,
        validate_event,
        validate_event_name,
    )
    assert StatsEvent is not None
    assert StatsEventError is not None
    assert callable(normalize_event_name)
    assert callable(validate_event_name)
    assert callable(make_event)
    assert callable(validate_event)


# ---------------------------------------------------------------------------
# Aucun accès base de données, fichier mvc/ ou tracking automatique
# ---------------------------------------------------------------------------


def test_aucun_acces_base_de_donnees():
    e = make_event("page_view", metadata={"path": "/accueil"})
    assert e.name == "page_view"


def test_aucun_tracking_automatique():
    e = make_event("form_submit")
    assert e.name == "form_submit"
    assert e.metadata == {}


def test_evenements_generiques_sans_metier_communes_sejours():
    events = [
        make_event("page_view",             label="Vue de page",    category="traffic"),
        make_event("contact_click",         label="Clic contact",   category="engagement"),
        make_event("form_submit",           label="Formulaire",     category="conversion"),
        make_event("download_click",        label="Téléchargement", category="engagement"),
        make_event("external_link_click",   label="Lien externe",   category="navigation"),
        make_event("media_view",            label="Média vu",       category="media"),
    ]
    for e in events:
        assert validate_event(e) is e
