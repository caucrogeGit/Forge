from __future__ import annotations


import pytest
pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats import (
    StatsAdminError,
    get_stats_events_admin_sql,
    list_stats_events,
    normalize_stats_event_row,
    prepare_stats_events_admin_params,
)


# ---------------------------------------------------------------------------
# Helpers de test
# ---------------------------------------------------------------------------

_SAMPLE_ROW = {
    "id": 1,
    "name": "page_view",
    "label": "Vue de page",
    "category": "traffic",
    "metadata": '{"path": "/contact"}',
    "created_at": "2026-05-08 10:00:00",
}


def fake_fetch_all(rows):
    def _fetch(sql, params):
        return rows
    return _fetch


# ---------------------------------------------------------------------------
# get_stats_events_admin_sql
# ---------------------------------------------------------------------------


def test_admin_sql_retourne_chaine():
    assert isinstance(get_stats_events_admin_sql(), str)


def test_admin_sql_lit_forge_stats_events():
    assert "forge_stats_events" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_id():
    assert "id" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_name():
    assert "name" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_label():
    assert "label" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_category():
    assert "category" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_metadata():
    assert "metadata" in get_stats_events_admin_sql()


def test_admin_sql_selectionne_created_at():
    assert "created_at" in get_stats_events_admin_sql()


def test_admin_sql_tri_created_at_desc():
    assert "created_at DESC" in get_stats_events_admin_sql()


def test_admin_sql_tri_id_desc():
    assert "id DESC" in get_stats_events_admin_sql()


def test_admin_sql_contient_limit():
    sql = get_stats_events_admin_sql()
    assert "LIMIT" in sql.upper()


def test_admin_sql_ajoute_filtre_name_si_fourni():
    sql = get_stats_events_admin_sql(name="page_view")
    assert "AND name = ?" in sql


def test_admin_sql_najoute_pas_filtre_name_si_absent():
    sql = get_stats_events_admin_sql()
    assert "AND name" not in sql


def test_admin_sql_ajoute_filtre_category_si_fourni():
    sql = get_stats_events_admin_sql(category="traffic")
    assert "AND category = ?" in sql


def test_admin_sql_najoute_pas_filtre_category_si_absent():
    sql = get_stats_events_admin_sql()
    assert "AND category" not in sql


def test_admin_sql_avec_deux_filtres():
    sql = get_stats_events_admin_sql(name="page_view", category="traffic")
    assert "AND name = ?" in sql
    assert "AND category = ?" in sql


# ---------------------------------------------------------------------------
# prepare_stats_events_admin_params
# ---------------------------------------------------------------------------


def test_params_sans_filtres_contient_limit():
    params = prepare_stats_events_admin_params()
    assert params == (50,)


def test_params_avec_name():
    params = prepare_stats_events_admin_params(name="page_view")
    assert params[0] == "page_view"
    assert params[-1] == 50


def test_params_avec_category():
    params = prepare_stats_events_admin_params(category="traffic")
    assert params[0] == "traffic"
    assert params[-1] == 50


def test_params_avec_name_et_category():
    params = prepare_stats_events_admin_params(name="page_view", category="traffic", limit=10)
    assert params == ("page_view", "traffic", 10)


def test_params_normalise_name():
    params = prepare_stats_events_admin_params(name="Page-View")
    assert params[0] == "page_view"


def test_params_refuse_name_invalide():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(name="<script>")


def test_params_refuse_category_vide():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(category="  ")


def test_params_refuse_category_non_chaine():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(category=123)


def test_params_refuse_limit_non_entier():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(limit="50")


def test_params_refuse_limit_bool():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(limit=True)


def test_params_refuse_limit_zero():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(limit=0)


def test_params_refuse_limit_negatif():
    with pytest.raises(StatsAdminError):
        prepare_stats_events_admin_params(limit=-1)


def test_params_borne_limit_a_500():
    params = prepare_stats_events_admin_params(limit=1000)
    assert params[-1] == 500


def test_params_accepte_limit_500():
    params = prepare_stats_events_admin_params(limit=500)
    assert params[-1] == 500


# ---------------------------------------------------------------------------
# normalize_stats_event_row
# ---------------------------------------------------------------------------


def test_normalize_accepte_ligne_valide():
    result = normalize_stats_event_row(_SAMPLE_ROW)
    assert result["id"] == 1
    assert result["name"] == "page_view"
    assert result["label"] == "Vue de page"
    assert result["category"] == "traffic"
    assert result["metadata"] == {"path": "/contact"}
    assert result["created_at"] == "2026-05-08 10:00:00"


def test_normalize_deserialise_metadata_json():
    row = {**_SAMPLE_ROW, "metadata": '{"key": "value"}'}
    result = normalize_stats_event_row(row)
    assert result["metadata"] == {"key": "value"}


def test_normalize_metadata_null_devient_dict_vide():
    row = {**_SAMPLE_ROW, "metadata": None}
    result = normalize_stats_event_row(row)
    assert result["metadata"] == {}


def test_normalize_metadata_chaine_vide_devient_dict_vide():
    row = {**_SAMPLE_ROW, "metadata": ""}
    result = normalize_stats_event_row(row)
    assert result["metadata"] == {}


def test_normalize_metadata_dict_passee_telle_quelle():
    row = {**_SAMPLE_ROW, "metadata": {"direct": True}}
    result = normalize_stats_event_row(row)
    assert result["metadata"] == {"direct": True}


def test_normalize_refuse_metadata_json_invalide():
    row = {**_SAMPLE_ROW, "metadata": "pas du json"}
    with pytest.raises(StatsAdminError, match="JSON"):
        normalize_stats_event_row(row)


def test_normalize_refuse_metadata_json_non_objet():
    row = {**_SAMPLE_ROW, "metadata": "[1, 2, 3]"}
    with pytest.raises(StatsAdminError):
        normalize_stats_event_row(row)


def test_normalize_refuse_ligne_incomplète():
    with pytest.raises(StatsAdminError, match="manquantes"):
        normalize_stats_event_row({"id": 1, "name": "page_view"})


def test_normalize_refuse_non_dict():
    with pytest.raises(StatsAdminError):
        normalize_stats_event_row(("page_view", "label"))


# ---------------------------------------------------------------------------
# list_stats_events
# ---------------------------------------------------------------------------


def test_list_stats_events_appelle_fetch_all():
    calls = []

    def recording_fetch(sql, params):
        calls.append((sql, params))
        return []

    list_stats_events(recording_fetch)
    assert len(calls) == 1


def test_list_stats_events_retourne_liste():
    result = list_stats_events(fake_fetch_all([]))
    assert isinstance(result, list)


def test_list_stats_events_retourne_dicts_normalises():
    result = list_stats_events(fake_fetch_all([_SAMPLE_ROW]))
    assert len(result) == 1
    assert result[0]["name"] == "page_view"
    assert isinstance(result[0]["metadata"], dict)


def test_list_stats_events_avec_filtre_name():
    calls = []

    def recording_fetch(sql, params):
        calls.append((sql, params))
        return []

    list_stats_events(recording_fetch, name="page_view")
    sql, params = calls[0]
    assert "AND name = ?" in sql
    assert "page_view" in params


def test_list_stats_events_avec_filtre_category():
    calls = []

    def recording_fetch(sql, params):
        calls.append((sql, params))
        return []

    list_stats_events(recording_fetch, category="traffic")
    sql, params = calls[0]
    assert "AND category = ?" in sql
    assert "traffic" in params


def test_list_stats_events_avec_limit():
    calls = []

    def recording_fetch(sql, params):
        calls.append((sql, params))
        return []

    list_stats_events(recording_fetch, limit=10)
    _, params = calls[0]
    assert params[-1] == 10


def test_list_stats_events_plusieurs_lignes():
    rows = [
        {**_SAMPLE_ROW, "id": 1, "name": "page_view"},
        {**_SAMPLE_ROW, "id": 2, "name": "contact_click"},
    ]
    result = list_stats_events(fake_fetch_all(rows))
    assert len(result) == 2
    assert result[0]["name"] == "page_view"
    assert result[1]["name"] == "contact_click"


# ---------------------------------------------------------------------------
# API publique importable depuis core.stats
# ---------------------------------------------------------------------------


def test_api_admin_importable():
    from forge_mvc_stats import (
        StatsAdminError,
        get_stats_events_admin_sql,
        list_stats_events,
        normalize_stats_event_row,
        prepare_stats_events_admin_params,
    )
    assert callable(get_stats_events_admin_sql)
    assert callable(prepare_stats_events_admin_params)
    assert callable(normalize_stats_event_row)
    assert callable(list_stats_events)
    assert StatsAdminError is not None


# ---------------------------------------------------------------------------
# Aucun accès base réel, tracking automatique, middleware ou admin graphique
# ---------------------------------------------------------------------------


def test_aucun_acces_base_de_donnees():
    result = list_stats_events(fake_fetch_all([]))
    assert result == []


def test_aucun_tracking_automatique():
    calls = []
    normalize_stats_event_row(_SAMPLE_ROW)
    assert len(calls) == 0


def test_aucun_middleware_ou_cookie():
    from forge_mvc_stats import admin
    source = open(admin.__file__).read()
    assert "middleware" not in source.lower()
    assert "cookie" not in source.lower()
    assert "session" not in source.lower()
    assert "request" not in source.lower()


def test_aucun_dashboard_graphique():
    from forge_mvc_stats import admin
    source = open(admin.__file__).read()
    assert "chart" not in source.lower()
    assert "graph" not in source.lower()
    assert "dashboard" not in source.lower()
