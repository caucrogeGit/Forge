from __future__ import annotations

from datetime import datetime

import pytest
pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats import (
    StatsEvent,
    StatsEventError,
    get_track_event_sql,
    make_event,
    prepare_track_event_values,
    track_event,
)


# ---------------------------------------------------------------------------
# Helpers de test
# ---------------------------------------------------------------------------


def fake_execute(calls: list):
    """Return a fake SQL executor that records (sql, params) into calls."""
    def _execute(sql, params):
        calls.append((sql, params))
    return _execute


# ---------------------------------------------------------------------------
# get_track_event_sql
# ---------------------------------------------------------------------------


def test_get_track_event_sql_retourne_chaine():
    assert isinstance(get_track_event_sql(), str)


def test_sql_contient_insert_into_forge_stats_events():
    assert "INSERT INTO forge_stats_events" in get_track_event_sql()


def test_sql_insere_name():
    assert "name" in get_track_event_sql()


def test_sql_insere_label():
    assert "label" in get_track_event_sql()


def test_sql_insere_category():
    assert "category" in get_track_event_sql()


def test_sql_insere_metadata():
    assert "metadata" in get_track_event_sql()


def test_sql_ninsere_pas_id():
    sql = get_track_event_sql()
    columns_part = sql[sql.index("("):sql.index("VALUES")]
    assert "id" not in columns_part


def test_sql_ninsere_pas_created_at():
    sql = get_track_event_sql()
    columns_part = sql[sql.index("("):sql.index("VALUES")]
    assert "created_at" not in columns_part


def test_sql_utilise_placeholder_point_dinterrogation():
    assert "?" in get_track_event_sql()


def test_sql_est_stable():
    assert get_track_event_sql() == get_track_event_sql()


# ---------------------------------------------------------------------------
# prepare_track_event_values
# ---------------------------------------------------------------------------


def test_prepare_accepte_stats_event_valide():
    e = make_event("page_view", label="Vue", category="traffic", metadata={"path": "/home"})
    values = prepare_track_event_values(e)
    assert isinstance(values, tuple)
    # + kind (STATS-EVENT-KIND-001). Le compte est vérifié contre le nombre de
    # marqueurs du SQL plutôt que contre un nombre écrit à la main : c'est leur
    # égalité qui compte, un décalage faisant échouer l'insertion.
    assert len(values) == get_track_event_sql().count("?")


def test_prepare_values_contient_name():
    e = make_event("page_view")
    values = prepare_track_event_values(e)
    assert values[0] == "page_view"


def test_prepare_values_contient_label():
    e = make_event("page_view", label="Vue de page")
    values = prepare_track_event_values(e)
    assert values[1] == "Vue de page"


def test_prepare_values_contient_category():
    e = make_event("page_view", category="traffic")
    values = prepare_track_event_values(e)
    assert values[2] == "traffic"


def test_prepare_values_metadata_serialisee_en_json():
    e = make_event("page_view", metadata={"path": "/contact"})
    values = prepare_track_event_values(e)
    import json
    parsed = json.loads(values[3])
    assert parsed["path"] == "/contact"


def test_prepare_values_metadata_vide_serialisee_en_json_vide():
    e = make_event("page_view")
    values = prepare_track_event_values(e)
    assert values[3] == "{}"


def test_prepare_values_metadata_json_stable():
    e = make_event("page_view", metadata={"z": 2, "a": 1})
    values = prepare_track_event_values(e)
    assert values[3] == '{"a": 1, "z": 2}'


def test_prepare_refuse_metadata_non_serialisable():
    e = make_event("page_view")
    object.__setattr__(e, "metadata", {"dt": datetime(2024, 1, 1)})
    with pytest.raises(StatsEventError, match="JSON"):
        prepare_track_event_values(e)


def test_prepare_refuse_non_stats_event():
    with pytest.raises(StatsEventError):
        prepare_track_event_values({"name": "page_view"})


def test_prepare_refuse_none():
    with pytest.raises(StatsEventError):
        prepare_track_event_values(None)


# ---------------------------------------------------------------------------
# track_event
# ---------------------------------------------------------------------------


def test_track_event_accepte_stats_event():
    calls = []
    e = make_event("page_view", label="Vue", category="traffic")
    result = track_event(fake_execute(calls), e)
    assert result is e
    assert len(calls) == 1


def test_track_event_accepte_nom_devenement():
    calls = []
    result = track_event(fake_execute(calls), "contact_click")
    assert isinstance(result, StatsEvent)
    assert result.name == "contact_click"
    assert len(calls) == 1


def test_track_event_accepte_chaine():
    calls = []
    result = track_event(fake_execute(calls), "page_view", label="Vue", category="traffic")
    assert result.name == "page_view"


def test_track_event_appelle_executeur_sql():
    calls = []
    track_event(fake_execute(calls), "page_view")
    assert len(calls) == 1
    sql, params = calls[0]
    assert "INSERT INTO forge_stats_events" in sql
    assert isinstance(params, tuple)
    assert len(params) == sql.count("?")


def test_track_event_retourne_evenement_valide():
    calls = []
    result = track_event(fake_execute(calls), "form_submit", label="Formulaire")
    assert isinstance(result, StatsEvent)
    assert result.name == "form_submit"
    assert result.label == "Formulaire"


def test_track_event_avec_metadata():
    calls = []
    track_event(
        fake_execute(calls),
        "page_view",
        label="Vue",
        category="traffic",
        metadata={"path": "/accueil"},
    )
    _, params = calls[0]
    import json
    assert json.loads(params[3])["path"] == "/accueil"


def test_track_event_refuse_nom_invalide():
    calls = []
    with pytest.raises(StatsEventError):
        track_event(fake_execute(calls), "<script>")
    assert len(calls) == 0


def test_track_event_refuse_objet_non_reconnu():
    calls = []
    with pytest.raises(StatsEventError):
        track_event(fake_execute(calls), 42)
    assert len(calls) == 0


def test_track_event_refuse_none():
    calls = []
    with pytest.raises(StatsEventError):
        track_event(fake_execute(calls), None)
    assert len(calls) == 0


def test_track_event_ne_cree_pas_connexion():
    calls = []
    track_event(fake_execute(calls), "page_view")
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# API publique importable depuis core.stats
# ---------------------------------------------------------------------------


def test_api_tracking_importable():
    from forge_mvc_stats import (
        get_track_event_sql,
        prepare_track_event_values,
        track_event,
    )
    assert callable(get_track_event_sql)
    assert callable(prepare_track_event_values)
    assert callable(track_event)


# ---------------------------------------------------------------------------
# Aucun tracking automatique, middleware, cookie, helper Jinja ou admin
# ---------------------------------------------------------------------------


def test_aucun_tracking_automatique():
    calls = []
    make_event("page_view")
    assert len(calls) == 0


def test_aucun_middleware_ou_cookie():
    from forge_mvc_stats import tracking
    source = open(tracking.__file__).read()
    assert "middleware" not in source.lower()
    assert "cookie" not in source.lower()
    assert "session" not in source.lower()
    assert "request" not in source.lower()


def test_aucun_helper_jinja():
    from forge_mvc_stats import tracking
    source = open(tracking.__file__).read()
    assert "jinja" not in source.lower()
    assert "globals" not in source.lower()


def test_aucun_dashboard_admin():
    from forge_mvc_stats import tracking
    source = open(tracking.__file__).read()
    assert "admin" not in source.lower()
    assert "controller" not in source.lower()
