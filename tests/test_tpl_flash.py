"""Contrat des messages flash standardisés — TPL-004."""

from __future__ import annotations

from pathlib import Path



ADMIN = Path("tests/fixtures/app/mvc/views/layouts/admin.html")
PUBLIC = Path("tests/fixtures/app/mvc/views/layouts/public.html")
BASE = Path("tests/fixtures/app/mvc/views/layouts/base.html")
ALERT = Path("tests/fixtures/app/mvc/views/components/alert.html")
FLASH_HELPER = Path("tests/fixtures/app/mvc/helpers/flash.py")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- alert.html toujours présent et complet ---


def test_alert_component_existe():
    assert ALERT.is_file()


def test_alert_contient_variant_success():
    assert "success" in _read(ALERT)


def test_alert_contient_variant_info():
    content = _read(ALERT)
    assert "info" in content or "blue" in content


def test_alert_contient_variant_warning():
    assert "warning" in _read(ALERT)


def test_alert_contient_variant_error():
    content = _read(ALERT)
    assert "error" in content or "danger" in content


# --- render_flash_html utilise components/alert.html ---


def test_flash_helper_utilise_alert_component():
    src = _read(FLASH_HELPER)
    assert "components/alert.html" in src


def test_flash_helper_ne_modifie_pas_partials_flash():
    src = _read(FLASH_HELPER)
    assert "partials/flash.html" not in src


def test_flash_helper_passe_message_et_type():
    src = _read(FLASH_HELPER)
    assert '"message"' in src
    assert '"type"' in src


# --- admin.html contient une zone flash ---


def test_admin_layout_contient_zone_flash():
    content = _read(ADMIN)
    assert "flash_html" in content


def test_admin_layout_flash_dans_main():
    content = _read(ADMIN)
    main_idx = content.index("<main")
    flash_idx = content.index("flash_html")
    endmain_idx = content.index("</main>")
    assert main_idx < flash_idx < endmain_idx


def test_admin_layout_flash_avant_block_content():
    content = _read(ADMIN)
    flash_idx = content.index("flash_html")
    content_idx = content.index("{% block content %}")
    assert flash_idx < content_idx


def test_admin_layout_flash_utilise_safe():
    content = _read(ADMIN)
    assert "flash_html | safe" in content


# --- public.html contient une zone flash ---


def test_public_layout_contient_zone_flash():
    content = _read(PUBLIC)
    assert "flash_html" in content


def test_public_layout_flash_dans_main():
    content = _read(PUBLIC)
    main_idx = content.index("<main")
    flash_idx = content.index("flash_html")
    endmain_idx = content.index("</main>")
    assert main_idx < flash_idx < endmain_idx


def test_public_layout_flash_avant_block_content():
    content = _read(PUBLIC)
    flash_idx = content.index("flash_html")
    content_idx = content.index("{% block content %}")
    assert flash_idx < content_idx


# --- base.html contient une zone flash ---


def test_base_layout_contient_zone_flash():
    content = _read(BASE)
    assert "flash_html" in content


# --- Contrat front : pas de comportements dynamiques ---


def test_layouts_flash_sans_htmx():
    for layout in [ADMIN, PUBLIC, BASE]:
        content = _read(layout)
        assert "htmx" not in content
        assert "hx-" not in content


def test_layouts_flash_sans_alpine():
    for layout in [ADMIN, PUBLIC, BASE]:
        content = _read(layout)
        assert "alpine" not in content
        assert "x-data" not in content


def test_layouts_conservent_app_js():
    for layout in [ADMIN, PUBLIC, BASE]:
        assert '<script src="/static/js/app.js" defer></script>' in _read(layout)


def test_layouts_conservent_scripts_block():
    for layout in [ADMIN, PUBLIC, BASE]:
        assert "{% block scripts %}{% endblock %}" in _read(layout)


# --- make:crud non modifié ---


def test_make_crud_flash_html_inchange():
    src = _read(Path("cli/entities/make_crud.py"))
    assert '"flash_html": render_flash_html(request)' in src


def test_aucune_cle_i18n_flash_ajoutee():
    import json
    catalog = json.loads(Path("tests/fixtures/app/translations/fr.json").read_text(encoding="utf-8"))
    for key in catalog:
        assert "flash" not in key.lower()
        assert "alerte" not in key.lower()
