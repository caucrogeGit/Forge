"""Tests — CRUD-RBAC-UI-001 : guards {% if can() %} dans les templates CRUD générés.

Vérifie que :
- avec rbac fourni, les boutons Nouveau/Modifier/Supprimer sont protégés par {% if can() %} ;
- sans rbac, aucun guard n'est injecté (compatibilité arrière) ;
- la permission correcte est utilisée pour chaque action ;
- le lien "Afficher" (show) n'est jamais conditionné (lecture libre) ;
- make_crud passe bien le rbac de la définition aux builders.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.crud.views_builder import (
    build_index_view,
    build_table_partial,
    build_show_view,
)

_DEFN_SIMPLE = {
    "entity": "Contact",
    "table": "contacts",
    "description": "",
    "fields": [
        {
            "name": "id", "column": "Id", "python_type": "int",
            "sql_type": "INT", "nullable": False, "primary_key": True,
            "auto_increment": True, "constraints": {}, "unique": False,
        },
        {
            "name": "nom", "column": "Nom", "python_type": "str",
            "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
            "auto_increment": False, "constraints": {}, "unique": False,
        },
    ],
}

_RBAC_FULL = {
    "permissions": {
        "index": "contacts.index",
        "show": "contacts.show",
        "create": "contacts.create",
        "store": "contacts.store",
        "edit": "contacts.edit",
        "update": "contacts.update",
        "delete": "contacts.delete",
    }
}

_DEFN_AVEC_RBAC = {**_DEFN_SIMPLE, "rbac": _RBAC_FULL}


# ---------------------------------------------------------------------------
# build_index_view — bouton Nouveau
# ---------------------------------------------------------------------------

class TestIndexViewGuard:
    def test_sans_rbac_pas_de_guard(self):
        html = build_index_view(_DEFN_SIMPLE)
        assert "{% if can(" not in html

    def test_avec_rbac_guard_present(self):
        html = build_index_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% if can('contacts.create') %}" in html

    def test_avec_rbac_endif_present(self):
        html = build_index_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% endif %}" in html

    def test_avec_rbac_bouton_entre_guard_et_endif(self):
        html = build_index_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        idx_if = html.index("{% if can('contacts.create') %}")
        idx_btn = html.index("button(", idx_if)
        idx_endif = html.index("{% endif %}", idx_if)
        assert idx_if < idx_btn < idx_endif

    def test_avec_rbac_sans_permission_create_pas_de_guard(self):
        rbac_sans_create = {"permissions": {"delete": "contacts.delete"}}
        html = build_index_view(_DEFN_SIMPLE, rbac=rbac_sans_create)
        assert "{% if can(" not in html


# ---------------------------------------------------------------------------
# build_table_partial — liens Modifier et Supprimer
# ---------------------------------------------------------------------------

class TestTablePartialGuard:
    def test_sans_rbac_pas_de_guard_edit(self):
        html = build_table_partial(_DEFN_SIMPLE)
        assert "{% if can(" not in html

    def test_avec_rbac_guard_edit_present(self):
        html = build_table_partial(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% if can('contacts.edit') %}" in html

    def test_avec_rbac_guard_delete_present(self):
        html = build_table_partial(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% if can('contacts.delete') %}" in html

    def test_avec_rbac_lien_show_toujours_present_sans_guard(self):
        html = build_table_partial(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "crud.show" in html
        idx_show = html.index("crud.show")
        before = html[:idx_show]
        # Tout bloc {% if can( %} avant le lien show doit être fermé par {% endif %} avant lui.
        # Le lien show lui-même n'est pas dans un bloc RBAC.
        last_if_idx = before.rfind("{% if can(")
        if last_if_idx == -1:
            return  # aucun guard — OK
        last_endif_idx = before.rfind("{% endif %}", last_if_idx)
        assert last_endif_idx > last_if_idx, (
            "Le lien 'show' semble être dans un bloc {% if can( %} non fermé."
        )

    def test_avec_rbac_edit_entre_guard_et_endif(self):
        html = build_table_partial(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        idx_if = html.index("{% if can('contacts.edit') %}")
        idx_lien = html.index("/edit", idx_if)
        idx_endif = html.index("{% endif %}", idx_if)
        assert idx_if < idx_lien < idx_endif

    def test_avec_rbac_delete_entre_guard_et_endif(self):
        html = build_table_partial(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        # Trouver le formulaire de suppression unitaire par ligne (distinct de /bulk-delete)
        idx_form = html.index("/destroy")
        # Trouver le guard {% if can %} immédiatement avant ce formulaire
        idx_if = html.rfind("{% if can('contacts.delete') %}", 0, idx_form)
        assert idx_if != -1, "Pas de guard avant le formulaire de suppression unitaire"
        idx_endif = html.index("{% endif %}", idx_if)
        assert idx_if < idx_form < idx_endif

    def test_avec_rbac_sans_permission_edit_pas_de_guard_edit(self):
        rbac_sans_edit = {"permissions": {"delete": "contacts.delete"}}
        html = build_table_partial(_DEFN_SIMPLE, rbac=rbac_sans_edit)
        assert "{% if can('contacts.delete') %}" in html
        assert "{% if can('contacts.edit') %}" not in html


# ---------------------------------------------------------------------------
# build_show_view — bouton Modifier et formulaire Supprimer
# ---------------------------------------------------------------------------

class TestShowViewGuard:
    def test_sans_rbac_pas_de_guard(self):
        html = build_show_view(_DEFN_SIMPLE)
        assert "{% if can(" not in html

    def test_avec_rbac_guard_edit_present(self):
        html = build_show_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% if can('contacts.edit') %}" in html

    def test_avec_rbac_guard_delete_present(self):
        html = build_show_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        assert "{% if can('contacts.delete') %}" in html

    def test_avec_rbac_edit_entre_guard_et_endif(self):
        html = build_show_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        idx_if = html.index("{% if can('contacts.edit') %}")
        idx_btn = html.index("button(", idx_if)
        idx_endif = html.index("{% endif %}", idx_if)
        assert idx_if < idx_btn < idx_endif

    def test_avec_rbac_delete_entre_guard_et_endif(self):
        html = build_show_view(_DEFN_SIMPLE, rbac=_RBAC_FULL)
        idx_if = html.index("{% if can('contacts.delete') %}")
        idx_form = html.index("/destroy", idx_if)
        idx_endif = html.index("{% endif %}", idx_if)
        assert idx_if < idx_form < idx_endif

    def test_avec_rbac_sans_permission_delete_pas_de_guard_delete(self):
        rbac_sans_delete = {"permissions": {"edit": "contacts.edit"}}
        html = build_show_view(_DEFN_SIMPLE, rbac=rbac_sans_delete)
        assert "{% if can('contacts.edit') %}" in html
        assert "{% if can('contacts.delete') %}" not in html


# ---------------------------------------------------------------------------
# Intégration make_crud — rbac de la définition transmis aux builders
# ---------------------------------------------------------------------------

class TestMakeCrudRbacIntegration:
    @classmethod
    def setup_class(cls):
        pytest.importorskip("forge_mvc_rbac")

    def test_make_crud_passe_rbac_index(self, tmp_path):
        import json
        from forge_mvc_entities.make_crud import make_crud

        entity_dir = tmp_path / "entities" / "contact"
        entity_dir.mkdir(parents=True)
        defn = {**_DEFN_AVEC_RBAC}
        (entity_dir / "contact.json").write_text(json.dumps(defn), encoding="utf-8")

        make_crud("contact", entities_root=tmp_path / "entities", output_root=tmp_path)
        index_html = (tmp_path / "mvc" / "views" / "contact" / "index.html").read_text()
        assert "{% if can('contacts.create') %}" in index_html

    def test_make_crud_passe_rbac_table(self, tmp_path):
        import json
        from forge_mvc_entities.make_crud import make_crud

        entity_dir = tmp_path / "entities" / "contact"
        entity_dir.mkdir(parents=True)
        (entity_dir / "contact.json").write_text(json.dumps(_DEFN_AVEC_RBAC), encoding="utf-8")

        make_crud("contact", entities_root=tmp_path / "entities", output_root=tmp_path)
        table_html = (tmp_path / "mvc" / "views" / "contact" / "_table.html").read_text()
        assert "{% if can('contacts.edit') %}" in table_html
        assert "{% if can('contacts.delete') %}" in table_html

    def test_make_crud_passe_rbac_show(self, tmp_path):
        import json
        from forge_mvc_entities.make_crud import make_crud

        entity_dir = tmp_path / "entities" / "contact"
        entity_dir.mkdir(parents=True)
        (entity_dir / "contact.json").write_text(json.dumps(_DEFN_AVEC_RBAC), encoding="utf-8")

        make_crud("contact", entities_root=tmp_path / "entities", output_root=tmp_path)
        show_html = (tmp_path / "mvc" / "views" / "contact" / "show.html").read_text()
        assert "{% if can('contacts.edit') %}" in show_html
        assert "{% if can('contacts.delete') %}" in show_html

    def test_make_crud_sans_rbac_pas_de_guards(self, tmp_path):
        import json
        from forge_mvc_entities.make_crud import make_crud

        entity_dir = tmp_path / "entities" / "contact"
        entity_dir.mkdir(parents=True)
        (entity_dir / "contact.json").write_text(json.dumps(_DEFN_SIMPLE), encoding="utf-8")

        make_crud("contact", entities_root=tmp_path / "entities", output_root=tmp_path)
        index_html = (tmp_path / "mvc" / "views" / "contact" / "index.html").read_text()
        table_html = (tmp_path / "mvc" / "views" / "contact" / "_table.html").read_text()
        show_html = (tmp_path / "mvc" / "views" / "contact" / "show.html").read_text()
        assert "{% if can(" not in index_html
        assert "{% if can(" not in table_html
        assert "{% if can(" not in show_html
