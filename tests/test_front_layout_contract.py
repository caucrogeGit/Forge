"""Contrat des zones JavaScript dans les layouts Forge."""

from __future__ import annotations

from pathlib import Path


LAYOUTS = [
    Path("mvc/views/layouts/base.html"),
    Path("mvc/views/layouts/public.html"),
    Path("mvc/views/layouts/admin.html"),
    Path("forge_cli/starters/data/carnet-contacts/files/mvc/views/layouts/app.html"),
    Path("forge_cli/starters/data/utilisateurs-auth/files/mvc/views/layouts/app.html"),
    Path("forge_cli/starters/data/suivi-comportement-eleves/files/mvc/views/layouts/app.html"),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_standard_layouts_reference_application_javascript():
    for layout in LAYOUTS:
        content = _read(layout)
        assert '<script src="/static/js/app.js" defer></script>' in content


def test_standard_layouts_expose_scripts_block_before_body_end():
    for layout in LAYOUTS:
        content = _read(layout)
        assert "{% block scripts %}{% endblock %}" in content
        assert content.index('{% block scripts %}{% endblock %}') < content.index("</body>")


def test_standard_layouts_do_not_require_htmx_or_alpine():
    forbidden = (
        "/static/vendor/htmx/htmx.min.js",
        "/static/vendor/alpine/alpine.min.js",
        "htmx.org",
        "alpinejs",
    )
    for layout in LAYOUTS:
        content = _read(layout)
        for value in forbidden:
            assert value not in content


def test_standard_layouts_do_not_add_dynamic_behaviors():
    for layout in LAYOUTS:
        content = _read(layout)
        assert "hx-" not in content
        assert "x-data" not in content
        assert "x-on" not in content


def test_make_crud_templates_do_not_inject_front_behaviors():
    make_crud = _read(Path("forge_cli/entities/make_crud.py"))

    assert "/static/vendor/htmx/htmx.min.js" not in make_crud
    assert "/static/vendor/alpine/alpine.min.js" not in make_crud
    assert "hx-delete" not in make_crud
    assert "hx-trigger" not in make_crud
    assert "x-data" not in make_crud


def test_front_documentation_mentions_scripts_block_and_optional_vendors():
    front_doc = _read(Path("docs/features/front.md"))

    assert '<script src="/static/js/app.js" defer></script>' in front_doc
    assert "{% block scripts %}{% endblock %}" in front_doc
    assert "HTMX ou Alpine.js" in front_doc


def test_front_documentation_explains_htmx_usage_without_runtime_changes():
    front_doc = _read(Path("docs/features/front.md"))

    assert "## Utiliser HTMX avec Forge" in front_doc
    assert '<script src="/static/vendor/htmx/htmx.min.js" defer></script>' in front_doc
    assert 'hx-get="/admin/contacts/fragment"' in front_doc
    assert 'hx-target="#resultat"' in front_doc
    assert 'hx-post="/contacts"' in front_doc
    assert 'hx-get="/contacts"' in front_doc
    assert 'hx-target="#crud-results"' in front_doc
    assert 'hx-trigger="keyup changed delay:300ms"' not in front_doc
    assert 'hx-post="/contacts/12/delete?page=1"' in front_doc
    assert 'hx-confirm="Confirmer la suppression ?"' in front_doc
    assert "ni `hx-delete`" in front_doc
    assert "hx-swap" in front_doc
    assert "contacts/_liste.html" in front_doc
    assert "Forge ne charge pas HTMX automatiquement" in front_doc
    assert "HTMX est optionnel" in front_doc
    assert "la recherche reste un formulaire GET classique" in front_doc
    assert "les liens de pagination restent HTML classiques" in front_doc
    assert 'hx-get="/contacts?page=2"' in front_doc
    assert "la recherche, la pagination et la suppression de liste" in front_doc
    assert "transformer Forge en SPA" in front_doc


def test_front_documentation_explains_alpine_usage_without_runtime_changes():
    front_doc = _read(Path("docs/features/front.md"))

    assert "## Utiliser Alpine.js avec Forge" in front_doc
    assert '<script src="/static/vendor/alpine/alpine.min.js" defer></script>' in front_doc
    assert "forge js:init alpine" in front_doc
    assert "{% block scripts %}{% endblock %}" in front_doc
    assert 'x-data="{ ouvert: false }"' in front_doc
    assert 'x-on:click="ouvert = !ouvert"' in front_doc
    assert 'x-show="ouvert"' in front_doc
    assert "x-bind" in front_doc
    assert "x-model" in front_doc
    assert "$event.preventDefault()" in front_doc
    assert "Alpine.js est optionnel" in front_doc
    assert "Forge ne charge pas Alpine automatiquement" in front_doc
    assert "la logique métier reste côté Python" in front_doc
    assert "Forge prépare Alpine.js mais ne génère pas encore de comportements Alpine" in front_doc
