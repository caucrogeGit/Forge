"""Tests — CRUD-SORT-001 : tri de colonnes CRUD généré.

Vérifie que :
- toutes les colonnes non-PK sont triables par défaut (_ALLOWED_SORT) ;
- la clé PK est aussi dans _ALLOWED_SORT ;
- le SQL ne concatène jamais sort directement (whitelist _ALLOWED_SORT.get) ;
- sort invalide est ignoré proprement (fallback _DEFAULT_SORT) ;
- direction invalide est normalisée à "asc" ;
- les liens de tri sont générés dans les en-têtes de colonnes ;
- les liens conservent q ;
- les liens conservent les filtres ;
- les liens NE conservent PAS page (tri réinitialise à la page 1) ;
- les liens portent les attributs HTMX (hx-get, hx-target, hx-swap, hx-push-url) ;
- le fallback href est présent sans HTMX ;
- la pagination conserve sort et direction ;
- le tri est compatible avec la suppression groupée.
"""
from __future__ import annotations

from forge_cli.entities.crud.model_builder import build_model
from forge_cli.entities.crud.views_builder import (
    build_table_partial,
    build_pagination_partial,
)
from forge_cli.entities.crud.controller_builder import build_controller
from forge_cli.entities.validation import normalize_entity_definition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_field(name, sql_type, python_type="str", nullable=False, list_meta=None):
    f = {
        "name": name, "sql_type": sql_type, "python_type": python_type,
        "nullable": nullable, "primary_key": False, "auto_increment": False,
        "constraints": {},
    }
    if list_meta is not None:
        f["list"] = list_meta
    return f


def _norm(fields=None):
    raw = {
        "format_version": 1, "entity": "Contact", "table": "contact",
        "description": "", "fields": [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
        ] + (fields or [
            _mk_field("nom", "VARCHAR(80)"),
            _mk_field("email", "VARCHAR(120)"),
        ]),
    }
    return normalize_entity_definition(raw, source="test.json")


def _entity_simple():
    return _norm()


def _entity_avec_filtre():
    return _norm([
        _mk_field("nom", "VARCHAR(80)"),
        _mk_field("statut", "VARCHAR(50)", list_meta={"filter": True}),
    ])


# ---------------------------------------------------------------------------
# Modèle — whitelist _ALLOWED_SORT
# ---------------------------------------------------------------------------

class TestAllowedSort:
    def test_allowed_sort_present(self):
        model = build_model(_entity_simple())
        assert "_ALLOWED_SORT" in model

    def test_colonnes_non_pk_dans_whitelist(self):
        model = build_model(_entity_simple())
        assert '"nom"' in model
        assert '"email"' in model

    def test_pk_dans_whitelist(self):
        model = build_model(_entity_simple())
        idx = model.find("_ALLOWED_SORT")
        bloc = model[idx: idx + 200]
        assert '"id"' in bloc

    def test_whitelist_complete_pour_deux_colonnes(self):
        model = build_model(_entity_simple())
        idx = model.find("_ALLOWED_SORT")
        bloc = model[idx: idx + 200]
        assert '"nom"' in bloc and '"email"' in bloc and '"id"' in bloc

    def test_default_sort_present(self):
        model = build_model(_entity_simple())
        assert "_DEFAULT_SORT" in model

    def test_default_sort_est_pk(self):
        model = build_model(_entity_simple())
        idx = model.find("_DEFAULT_SORT")
        bloc = model[idx: idx + 80]
        assert "Id" in bloc or "id" in bloc.lower()


# ---------------------------------------------------------------------------
# Modèle — SQL sécurisée (aucune concaténation directe)
# ---------------------------------------------------------------------------

class TestSQLSécurisée:
    def test_find_paginated_utilise_allowed_sort_get(self):
        model = build_model(_entity_simple())
        assert "_ALLOWED_SORT.get" in model

    def test_find_paginated_utilise_default_sort(self):
        model = build_model(_entity_simple())
        assert "_DEFAULT_SORT" in model
        idx = model.find("_ALLOWED_SORT.get")
        bloc = model[idx: idx + 80]
        assert "_DEFAULT_SORT" in bloc

    def test_order_by_sans_concatenation_directe_du_sort_utilisateur(self):
        model = build_model(_entity_simple())
        idx = model.find("def find_contacts_paginated")
        bloc = model[idx: idx + 1500]
        assert "ORDER BY" in bloc
        assert "sort_col" in bloc
        assert "sort_col = _ALLOWED_SORT.get" in bloc

    def test_direction_par_asc_ou_desc_uniquement(self):
        model = build_model(_entity_simple())
        idx = model.find("def find_contacts_paginated")
        bloc = model[idx: idx + 700]
        assert '"DESC"' in bloc or '"ASC"' in bloc
        assert "sort_dir" in bloc

    def test_direction_desc_si_direction_eq_desc(self):
        model = build_model(_entity_simple())
        idx = model.find("def find_contacts_paginated")
        bloc = model[idx: idx + 700]
        assert 'direction == "desc"' in bloc


# ---------------------------------------------------------------------------
# Contrôleur — validation sort et direction
# ---------------------------------------------------------------------------

class TestControleurValidation:
    def test_sort_valide_par_whitelist(self):
        ctrl = build_controller(_entity_simple())
        assert '"nom"' in ctrl or "nom" in ctrl
        idx = ctrl.find("sort")
        assert idx != -1

    def test_sort_invalide_remplace_par_vide(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find('sort not in')
        assert idx != -1
        bloc = ctrl[idx: idx + 60]
        assert 'sort = ""' in bloc or "sort = ''" in bloc

    def test_direction_validee_asc_desc(self):
        ctrl = build_controller(_entity_simple())
        assert '"asc"' in ctrl and '"desc"' in ctrl
        assert 'direction not in ("asc", "desc")' in ctrl

    def test_direction_invalide_normalisee_asc(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find('direction not in ("asc", "desc")')
        bloc = ctrl[idx: idx + 60]
        assert '"asc"' in bloc

    def test_sort_transmis_au_modele(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("find_contacts_paginated(")
        bloc = ctrl[idx: idx + 100]
        assert "sort=sort" in bloc

    def test_direction_transmis_au_modele(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("find_contacts_paginated(")
        bloc = ctrl[idx: idx + 100]
        assert "direction=direction" in bloc

    def test_sort_inclus_dans_pagination_dict(self):
        ctrl = build_controller(_entity_simple())
        assert '"sort": sort' in ctrl

    def test_direction_incluse_dans_pagination_dict(self):
        ctrl = build_controller(_entity_simple())
        assert '"direction": direction' in ctrl


# ---------------------------------------------------------------------------
# Vue — liens de tri dans les en-têtes
# ---------------------------------------------------------------------------

class TestLiensDeTri:
    def test_lien_sort_dans_thead(self):
        html = build_table_partial(_entity_simple())
        assert "?sort=nom" in html

    def test_deux_colonnes_ont_liens_de_tri(self):
        html = build_table_partial(_entity_simple())
        assert "?sort=nom" in html
        assert "?sort=email" in html

    def test_lien_direction_asc_par_defaut(self):
        html = build_table_partial(_entity_simple())
        assert "direction=asc" in html

    def test_lien_inverse_direction_si_colonne_active(self):
        html = build_table_partial(_entity_simple())
        assert "pagination.direction == 'asc'" in html or "pagination.direction ==" in html

    def test_indicateur_direction_dans_lien(self):
        html = build_table_partial(_entity_simple())
        assert "↑" in html and "↓" in html

    def test_lien_sort_conserve_q(self):
        html = build_table_partial(_entity_simple())
        idx = html.find("?sort=nom")
        bloc = html[idx: idx + 300]
        assert "pagination.q" in bloc

    def test_lien_sort_conserve_filtres(self):
        defn = _entity_avec_filtre()
        html = build_table_partial(defn)
        idx = html.find("?sort=nom")
        bloc = html[idx: idx + 400]
        assert "pagination.filters" in bloc

    def test_lien_sort_ne_conserve_pas_page(self):
        html = build_table_partial(_entity_simple())
        idx = html.find("?sort=nom")
        assert idx != -1
        bloc_avant_direction = html[idx: idx + 400]
        assert "pagination.page" not in bloc_avant_direction

    def test_href_present(self):
        html = build_table_partial(_entity_simple())
        assert 'href="?sort=nom' in html

    def test_hx_get_present(self):
        html = build_table_partial(_entity_simple())
        assert 'hx-get="?sort=nom' in html

    def test_hx_target_crud_results(self):
        html = build_table_partial(_entity_simple())
        # hx-target est sur le même lien <a>, après le hx-get
        idx_th = html.find('?sort=nom')
        th_end = html.find("</th>", idx_th)
        bloc = html[idx_th: th_end]
        assert 'hx-target="#crud-results"' in bloc

    def test_hx_swap_innerhtml(self):
        html = build_table_partial(_entity_simple())
        idx_th = html.find('?sort=nom')
        th_end = html.find("</th>", idx_th)
        bloc = html[idx_th: th_end]
        assert 'hx-swap="innerHTML"' in bloc

    def test_hx_push_url_true(self):
        html = build_table_partial(_entity_simple())
        idx_th = html.find('?sort=nom')
        th_end = html.find("</th>", idx_th)
        bloc = html[idx_th: th_end]
        assert 'hx-push-url="true"' in bloc

    def test_href_et_hx_get_meme_url(self):
        html = build_table_partial(_entity_simple())
        idx_href = html.find('href="?sort=nom')
        idx_hxget = html.find('hx-get="?sort=nom', idx_href)
        assert idx_href != -1
        assert idx_hxget != -1
        # Les deux doivent être dans le même th
        th_start = html.rfind("<th", 0, idx_href)
        th_end = html.find("</th>", idx_href)
        assert th_start < idx_hxget < th_end


# ---------------------------------------------------------------------------
# Pagination — conservation sort et direction
# ---------------------------------------------------------------------------

class TestPaginationConservationSort:
    def test_pagination_conserve_sort(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.sort" in html

    def test_pagination_conserve_direction(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.direction" in html

    def test_pagination_lien_prev_contient_sort(self):
        html = build_pagination_partial(_entity_simple())
        assert "pagination.sort" in html and "pagination.direction" in html

    def test_pagination_hx_get_present(self):
        html = build_pagination_partial(_entity_simple())
        assert "hx-get=" in html

    def test_pagination_fallback_href_present(self):
        html = build_pagination_partial(_entity_simple())
        assert "href=" in html


# ---------------------------------------------------------------------------
# Compatibilité — tri + filtres + suppression groupée
# ---------------------------------------------------------------------------

class TestCompatibilite:
    def test_table_avec_filtre_et_tri(self):
        defn = _entity_avec_filtre()
        html = build_table_partial(defn)
        assert "?sort=nom" in html
        assert 'id="bulk-delete-form"' in html
        assert "pagination.filters" in html

    def test_bulk_delete_form_toujours_present_avec_tri(self):
        html = build_table_partial(_entity_simple())
        assert 'id="bulk-delete-form"' in html
        assert "?sort=nom" in html

    def test_checkbox_presente_avec_tri(self):
        html = build_table_partial(_entity_simple())
        assert 'type="checkbox"' in html

    def test_pas_de_script_dans_table(self):
        html = build_table_partial(_entity_simple())
        assert "<script" not in html
