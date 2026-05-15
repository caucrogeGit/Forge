"""Tests — CRUD-BULK-DELETE-001 : suppression groupée CRUD minimale.

Vérifie les critères d'acceptation du ticket CRUD-BULK-DELETE-001 :

- cases à cocher générées dans la table ;
- attribut form="bulk-delete-form" sur les cases ;
- formulaire bulk-delete-form présent avec CSRF et action /bulk-delete ;
- bouton "Supprimer la sélection" présent ;
- bouton conditionné par can(...) si RBAC actif ;
- route POST /bulk-delete dans le bloc de routes ;
- route POST /bulk-delete/confirm dans le bloc de routes ;
- template bulk_delete_confirm.html généré ;
- CSRF dans le template de confirmation ;
- hidden inputs ids dans la confirmation ;
- bouton confirmer et lien annuler présents ;
- modèle contient bulk_delete_{plural} avec placeholders SQL ;
- contrôleur contient bulk_delete et bulk_delete_confirm ;
- _parse_bulk_ids valide les IDs ;
- import bulk_delete_{plural} dans le contrôleur ;
- CRUD sans RBAC reste fonctionnel ;
- aucun JS personnalisé ;
- aucun HTMX obligatoire dans la suppression groupée.
"""
from __future__ import annotations

import pytest

from forge_cli.entities.make_crud import (
    build_bulk_delete_confirm_view,
    build_controller,
    build_model,
    build_table_partial,
    _route_block,
)
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


def _norm(fields=None, rbac=None):
    raw = {
        "format_version": 1, "entity": "Contact", "table": "contact",
        "description": "", "fields": [
            {"name": "id", "sql_type": "INT", "python_type": "int",
             "primary_key": True, "auto_increment": True, "nullable": False, "constraints": {}},
        ] + (fields or [_mk_field("nom", "VARCHAR(80)")]),
    }
    if rbac:
        raw["rbac"] = rbac
    return normalize_entity_definition(raw, source="test.json")


def _entity_simple():
    return _norm()


def _entity_with_rbac():
    return _norm(rbac={"permissions": {"delete": "contact.delete"}})


def _rbac_from(definition):
    return definition.get("rbac")


def _entity_with_filter():
    return _norm([_mk_field("statut", "VARCHAR(50)", list_meta={"filter": True})])


# ---------------------------------------------------------------------------
# Table — cases à cocher
# ---------------------------------------------------------------------------

class TestCasesACocher:
    def test_checkbox_present_dans_table(self):
        html = build_table_partial(_entity_simple())
        assert 'type="checkbox"' in html

    def test_name_ids_sur_checkbox(self):
        html = build_table_partial(_entity_simple())
        assert 'name="ids"' in html

    def test_form_attribute_sur_checkbox(self):
        html = build_table_partial(_entity_simple())
        assert 'form="bulk-delete-form"' in html

    def test_value_pk_sur_checkbox(self):
        html = build_table_partial(_entity_simple())
        assert "contact.Id" in html

    def test_checkbox_dans_tbody(self):
        html = build_table_partial(_entity_simple())
        tbody_start = html.find("<tbody")
        assert tbody_start != -1
        checkbox_pos = html.find('type="checkbox"', tbody_start)
        assert checkbox_pos != -1

    def test_th_vide_en_premiere_colonne(self):
        html = build_table_partial(_entity_simple())
        thead_start = html.find("<thead")
        thead_end = html.find("</thead>")
        thead = html[thead_start:thead_end]
        # Le premier <th> est le header vide de la colonne checkbox
        first_th = thead.find("<th")
        assert first_th != -1
        # Il doit être vide (pas de texte de colonne)
        th_content_end = thead.find("</th>", first_th)
        th_block = thead[first_th:th_content_end]
        assert "w-10" in th_block


# ---------------------------------------------------------------------------
# Formulaire bulk-delete-form
# ---------------------------------------------------------------------------

class TestFormulaireBulkDelete:
    def test_form_id_present(self):
        html = build_table_partial(_entity_simple())
        assert 'id="bulk-delete-form"' in html

    def test_form_method_post(self):
        html = build_table_partial(_entity_simple())
        form_idx = html.find('id="bulk-delete-form"')
        assert form_idx != -1
        form_tag_start = html.rfind("<form", 0, form_idx)
        form_tag_end = html.find(">", form_tag_start)
        form_tag = html[form_tag_start:form_tag_end + 1]
        assert 'method="post"' in form_tag

    def test_form_action_bulk_delete(self):
        html = build_table_partial(_entity_simple())
        assert 'action="/contacts/bulk-delete"' in html

    def test_csrf_dans_formulaire(self):
        html = build_table_partial(_entity_simple())
        assert 'name="csrf_token"' in html and '{{ csrf_token }}' in html

    def test_bouton_supprimer_selection_present(self):
        html = build_table_partial(_entity_simple())
        assert "Supprimer la sélection" in html

    def test_bouton_type_submit(self):
        html = build_table_partial(_entity_simple())
        assert 'type="submit"' in html


# ---------------------------------------------------------------------------
# RBAC — bouton conditionné
# ---------------------------------------------------------------------------

class TestRBACBulkDelete:
    def test_sans_rbac_bouton_toujours_visible(self):
        defn = _entity_simple()
        html = build_table_partial(defn, rbac=_rbac_from(defn))
        assert "Supprimer la sélection" in html
        assert "{% if can(" not in html.split("Supprimer")[0].split('<form id="bulk-delete-form"')[-1]

    def test_avec_rbac_bouton_conditionne(self):
        defn = _entity_with_rbac()
        html = build_table_partial(defn, rbac=_rbac_from(defn))
        assert "Supprimer la sélection" in html
        assert "can('contact.delete')" in html

    def test_avec_rbac_form_dans_bloc_conditionnel(self):
        defn = _entity_with_rbac()
        html = build_table_partial(defn, rbac=_rbac_from(defn))
        perm_idx = html.find("can('contact.delete')")
        form_idx = html.find('id="bulk-delete-form"')
        # La permission précède le formulaire
        assert perm_idx < form_idx

    def test_avec_rbac_checkbox_conditionnee(self):
        defn = _entity_with_rbac()
        html = build_table_partial(defn, rbac=_rbac_from(defn))
        # La checkbox dans tbody doit être conditionnée par can(...)
        tbody_idx = html.find("<tbody")
        section = html[tbody_idx:]
        assert "can('contact.delete')" in section

    def test_sans_rbac_pas_de_can(self):
        defn = _entity_simple()
        html = build_table_partial(defn, rbac=_rbac_from(defn))
        # Sans RBAC configuré, pas de can() sur la suppression groupée
        assert "can(" not in html or "can('contact.delete')" not in html


# ---------------------------------------------------------------------------
# Template de confirmation
# ---------------------------------------------------------------------------

class TestTemplateConfirmation:
    def test_template_genere(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert len(html) > 100

    def test_extends_layout(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert '{% extends "layouts/app.html" %}' in html

    def test_form_confirmation_present(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert 'action="/contacts/bulk-delete/confirm"' in html

    def test_form_method_post(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert 'method="post"' in html

    def test_csrf_dans_confirmation(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert 'name="csrf_token"' in html
        assert '{{ csrf_token }}' in html

    def test_hidden_ids_dans_confirmation(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert 'name="ids"' in html
        assert '{% for id in ids %}' in html

    def test_count_affiche(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert '{{ count }}' in html

    def test_bouton_confirmer_present(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert "Confirmer" in html
        assert 'type="submit"' in html

    def test_lien_annuler_present(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert "Annuler" in html
        assert 'href="/contacts"' in html

    def test_message_irreversible(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert "irréversible" in html or "définitive" in html

    def test_pas_de_script(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert "<script" not in html

    def test_pas_de_htmx(self):
        html = build_bulk_delete_confirm_view(_entity_simple())
        assert "hx-" not in html


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class TestRoutes:
    def test_route_bulk_delete_presente(self):
        bloc = _route_block(_entity_simple())
        assert "/bulk-delete" in bloc

    def test_route_bulk_delete_confirm_presente(self):
        bloc = _route_block(_entity_simple())
        assert "/bulk-delete/confirm" in bloc

    def test_route_bulk_delete_est_post(self):
        bloc = _route_block(_entity_simple())
        assert '"POST"' in bloc and "bulk_delete" in bloc

    def test_route_bulk_delete_confirm_est_post(self):
        bloc = _route_block(_entity_simple())
        assert '"POST"' in bloc and "bulk_delete_confirm" in bloc

    def test_routes_existantes_intactes(self):
        bloc = _route_block(_entity_simple())
        assert "index" in bloc
        assert "create" in bloc
        assert "destroy" in bloc


# ---------------------------------------------------------------------------
# Modèle — bulk_delete SQL paramétré
# ---------------------------------------------------------------------------

class TestModeleSQL:
    def test_bulk_delete_contacts_presente(self):
        model = build_model(_entity_simple())
        assert "def bulk_delete_contacts" in model

    def test_placeholders_sql(self):
        model = build_model(_entity_simple())
        idx = model.find("def bulk_delete_contacts")
        bloc = model[idx: idx + 400]
        assert "?" in bloc
        assert "placeholders" in bloc

    def test_in_clause(self):
        model = build_model(_entity_simple())
        assert "IN (" in model or "IN(" in model

    def test_pas_de_concatenation_directe(self):
        model = build_model(_entity_simple())
        idx = model.find("def bulk_delete_contacts")
        bloc = model[idx: idx + 400]
        # La requête ne doit pas contenir d'IDs directement concaténés
        assert 'f"DELETE' not in bloc or "placeholders" in bloc

    def test_return_si_vide(self):
        model = build_model(_entity_simple())
        idx = model.find("def bulk_delete_contacts")
        bloc = model[idx: idx + 200]
        assert "if not ids" in bloc
        assert "return" in bloc

    def test_utilise_api_canonique(self):
        model = build_model(_entity_simple())
        idx = model.find("def bulk_delete_contacts")
        bloc = model[idx: idx + 600]
        assert 'execute("DELETE FROM' in bloc
        assert "get_connection" not in bloc


# ---------------------------------------------------------------------------
# Contrôleur — méthodes bulk
# ---------------------------------------------------------------------------

class TestControleurBulk:
    def test_import_bulk_delete_contacts(self):
        ctrl = build_controller(_entity_simple())
        assert "bulk_delete_contacts" in ctrl

    def test_methode_bulk_delete_presente(self):
        ctrl = build_controller(_entity_simple())
        assert "def bulk_delete(request)" in ctrl

    def test_methode_bulk_delete_confirm_presente(self):
        ctrl = build_controller(_entity_simple())
        assert "def bulk_delete_confirm(request)" in ctrl

    def test_parse_bulk_ids_presente(self):
        ctrl = build_controller(_entity_simple())
        assert "_parse_bulk_ids" in ctrl

    def test_redirect_si_aucun_id(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("def bulk_delete(request)")
        bloc = ctrl[idx: idx + 300]
        assert "redirect_with_flash" in bloc
        assert "Aucun élément" in bloc

    def test_bulk_delete_confirm_appelle_bulk_delete_contacts(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("def bulk_delete_confirm(request)")
        bloc = ctrl[idx: idx + 300]
        assert "bulk_delete_contacts" in bloc

    def test_parse_bulk_ids_valide_entiers(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("_parse_bulk_ids")
        bloc = ctrl[idx: idx + 400]
        assert "int(v)" in bloc

    def test_parse_bulk_ids_deduplique(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("_parse_bulk_ids")
        bloc = ctrl[idx: idx + 400]
        assert "seen" in bloc

    def test_parse_bulk_ids_ignore_negatifs(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("_parse_bulk_ids")
        bloc = ctrl[idx: idx + 700]
        assert "<= 0" in bloc or "< 0" in bloc

    def test_bulk_delete_rend_template_confirmation(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("def bulk_delete(request)")
        bloc = ctrl[idx: idx + 300]
        assert "bulk_delete_confirm.html" in bloc

    def test_sans_rbac_pas_de_require_permission_sur_bulk(self):
        ctrl = build_controller(_entity_simple())
        idx = ctrl.find("def bulk_delete(request)")
        # Les 2 lignes avant ne doivent pas contenir require_permission
        before = ctrl[max(0, idx - 100): idx]
        assert "require_permission" not in before

    def test_avec_rbac_require_permission_sur_bulk_delete(self):
        pytest.importorskip("forge_mvc_rbac")
        defn = _entity_with_rbac()
        ctrl = build_controller(defn)
        idx = ctrl.find("def bulk_delete(request)")
        before = ctrl[max(0, idx - 150): idx]
        assert "require_permission" in before
        assert "contact.delete" in before

    def test_avec_rbac_require_permission_sur_bulk_confirm(self):
        pytest.importorskip("forge_mvc_rbac")
        defn = _entity_with_rbac()
        ctrl = build_controller(defn)
        idx = ctrl.find("def bulk_delete_confirm(request)")
        before = ctrl[max(0, idx - 150): idx]
        assert "require_permission" in before


# ---------------------------------------------------------------------------
# Compatibilité avec filtres et CRUD sans RBAC
# ---------------------------------------------------------------------------

class TestCompatibilite:
    def test_table_avec_filtres_toujours_valide(self):
        defn = _entity_with_filter()
        html = build_table_partial(defn)
        assert 'type="checkbox"' in html
        assert 'id="bulk-delete-form"' in html

    def test_pas_de_script_dans_table(self):
        html = build_table_partial(_entity_simple())
        assert "<script" not in html

    def test_pas_de_hx_trigger_dans_bulk(self):
        html = build_table_partial(_entity_simple())
        assert "hx-trigger" not in html

    def test_pas_de_keyup_dans_bulk(self):
        html = build_table_partial(_entity_simple())
        assert "keyup" not in html

    def test_pas_de_debounce_dans_bulk(self):
        html = build_table_partial(_entity_simple())
        assert "debounce" not in html

    def test_suppression_unitaire_toujours_presente(self):
        html = build_table_partial(_entity_simple())
        # La suppression unitaire (destroy) doit coexister avec la suppression groupée
        assert "/delete" in html

    def test_form_bulk_utilise_html5_form_attribute(self):
        # Les cases référencent le formulaire via l'attribut form= (HTML5, pas de nesting)
        html = build_table_partial(_entity_simple())
        assert 'form="bulk-delete-form"' in html
        # Vérifier que les checkboxes ne sont PAS dans le form bulk-delete-form (pas de nesting)
        form_start = html.find('<form id="bulk-delete-form"')
        form_end = html.find("</form>", form_start) + len("</form>")
        form_content = html[form_start:form_end]
        # La checkbox n'est pas dans le form (elle l'est seulement en apparence, via form=)
        assert 'type="checkbox"' not in form_content
