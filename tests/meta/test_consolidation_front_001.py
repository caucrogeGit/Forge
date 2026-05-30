"""Tests pour CONSOLIDATION-FRONT-001 — Tailwind / HTMX / Alpine / templates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Tailwind CSS ───────────────────────────────────────────────────────────────

def test_package_json_existe():
    """package.json existe à la racine du projet."""
    assert (ROOT / "package.json").exists()


def test_package_json_contient_tailwind():
    """package.json déclare tailwindcss comme dépendance."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "tailwindcss" in pkg.get("dependencies", {}) or "tailwindcss" in pkg.get("devDependencies", {})


def test_package_json_contient_script_build_css():
    """package.json déclare le script build:css."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "build:css" in pkg.get("scripts", {})


def test_static_src_input_css_existe():
    """static/src/input.css existe (source Tailwind)."""
    assert (ROOT / "static" / "src" / "input.css").exists()


def test_static_tailwind_css_existe():
    """static/tailwind.css existe (CSS compilé)."""
    assert (ROOT / "static" / "tailwind.css").exists()


def test_input_css_importe_tailwind():
    """static/src/input.css commence par @import tailwindcss."""
    content = (ROOT / "static" / "src" / "input.css").read_text(encoding="utf-8")
    assert "tailwindcss" in content


def test_app_js_existe_et_ne_charge_pas_htmx_alpine():
    """static/js/app.js existe et n'impose pas HTMX ou Alpine."""
    app_js = ROOT / "static" / "js" / "app.js"
    assert app_js.exists()
    content = app_js.read_text(encoding="utf-8").lower()
    assert "htmx" not in content
    assert "alpine" not in content


# ── forge js:init ─────────────────────────────────────────────────────────────

def test_js_init_htmx_ajoute_dependance_npm(tmp_path):
    """forge js:init htmx ajoute htmx.org dans package.json."""
    from forge_cli.front import init_htmx, HTMX_PACKAGE, HTMX_VERSION
    pkg_path = tmp_path / "package.json"
    pkg_path.write_text(json.dumps({"scripts": {}, "dependencies": {}}, indent=2), encoding="utf-8")
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True)

    init_htmx(tmp_path)

    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    assert HTMX_PACKAGE in pkg["dependencies"]
    assert pkg["dependencies"][HTMX_PACKAGE] == HTMX_VERSION


def test_js_init_htmx_cree_dossier_vendor(tmp_path):
    """forge js:init htmx crée static/vendor/htmx/."""
    from forge_cli.front import init_htmx
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {}, "dependencies": {}}, indent=2), encoding="utf-8"
    )
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True)

    init_htmx(tmp_path)

    assert (tmp_path / "static" / "vendor" / "htmx").is_dir()


def test_js_init_alpine_ajoute_dependance_npm(tmp_path):
    """forge js:init alpine ajoute alpinejs dans package.json."""
    from forge_cli.front import init_alpine, ALPINE_PACKAGE, ALPINE_VERSION
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {}, "dependencies": {}}, indent=2), encoding="utf-8"
    )
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True)

    init_alpine(tmp_path)

    pkg = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert ALPINE_PACKAGE in pkg["dependencies"]
    assert pkg["dependencies"][ALPINE_PACKAGE] == ALPINE_VERSION


def test_js_init_htmx_alpine_initialise_les_deux(tmp_path):
    """forge js:init htmx-alpine initialise HTMX et Alpine ensemble."""
    from forge_cli.front import init_htmx_alpine, HTMX_PACKAGE, ALPINE_PACKAGE
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {}, "dependencies": {}}, indent=2), encoding="utf-8"
    )
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True)

    result = init_htmx_alpine(tmp_path)

    pkg = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert HTMX_PACKAGE in pkg["dependencies"]
    assert ALPINE_PACKAGE in pkg["dependencies"]
    assert "htmx" in result
    assert "alpine" in result


def test_js_init_htmx_idempotent(tmp_path):
    """forge js:init htmx est idempotent — appels multiples sans effet de bord."""
    from forge_cli.front import init_htmx, HTMX_PACKAGE
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {}, "dependencies": {}}, indent=2), encoding="utf-8"
    )
    (tmp_path / "mvc" / "views" / "layouts").mkdir(parents=True)

    init_htmx(tmp_path)
    version_after_1 = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))["dependencies"][HTMX_PACKAGE]
    init_htmx(tmp_path)
    version_after_2 = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))["dependencies"][HTMX_PACKAGE]

    assert version_after_1 == version_after_2


def test_js_init_commande_inconnue_leve_sysexit():
    """forge js:init avec une commande inconnue lève SystemExit."""
    from forge_cli.front import main
    with pytest.raises(SystemExit):
        main(["js:init", "react"])


def test_htmx_vendor_non_committe_par_defaut():
    """static/vendor/htmx/htmx.min.js n'est pas présent dans le dépôt (doit être installé)."""
    assert not (ROOT / "static" / "vendor" / "htmx" / "htmx.min.js").exists()


def test_alpine_vendor_non_committe_par_defaut():
    """static/vendor/alpine/alpine.min.js n'est pas présent dans le dépôt (doit être installé)."""
    assert not (ROOT / "static" / "vendor" / "alpine" / "alpine.min.js").exists()


# ── Layouts Jinja ─────────────────────────────────────────────────────────────

LAYOUT_PATHS = [
    ROOT / "mvc" / "views" / "layouts" / "base.html",
    ROOT / "mvc" / "views" / "layouts" / "admin.html",
    ROOT / "mvc" / "views" / "layouts" / "public.html",
]


@pytest.mark.parametrize("layout_path", LAYOUT_PATHS)
def test_layout_existe(layout_path):
    """Les layouts principaux existent."""
    assert layout_path.exists(), f"Layout absent : {layout_path.name}"


@pytest.mark.parametrize("layout_path", LAYOUT_PATHS)
def test_layout_charge_tailwind_css(layout_path):
    """Chaque layout charge static/tailwind.css."""
    content = layout_path.read_text(encoding="utf-8")
    assert "tailwind.css" in content, f"tailwind.css absent dans {layout_path.name}"


@pytest.mark.parametrize("layout_path", LAYOUT_PATHS)
def test_layout_expose_bloc_scripts(layout_path):
    """Chaque layout expose {% block scripts %} pour les scripts optionnels."""
    content = layout_path.read_text(encoding="utf-8")
    assert "block scripts" in content, f"Bloc scripts absent dans {layout_path.name}"


@pytest.mark.parametrize("layout_path", LAYOUT_PATHS)
def test_layout_ne_charge_pas_htmx_automatiquement(layout_path):
    """Les layouts n'injectent pas HTMX automatiquement — chargement explicite requis."""
    content = layout_path.read_text(encoding="utf-8")
    assert "htmx.min.js" not in content, f"htmx.min.js trouvé dans {layout_path.name}"
    assert "htmx.org" not in content, f"htmx.org trouvé dans {layout_path.name}"


@pytest.mark.parametrize("layout_path", LAYOUT_PATHS)
def test_layout_ne_charge_pas_alpine_automatiquement(layout_path):
    """Les layouts n'injectent pas Alpine automatiquement — chargement explicite requis."""
    content = layout_path.read_text(encoding="utf-8")
    assert "alpine.min.js" not in content, f"alpine.min.js trouvé dans {layout_path.name}"


# ── CRUD HTMX ─────────────────────────────────────────────────────────────────

def test_make_crud_genere_hx_get_pour_pagination():
    """make_crud génère hx-get pour la pagination (amélioration progressive)."""
    content = (ROOT / "forge_cli" / "entities" / "make_crud.py").read_text(encoding="utf-8")
    assert "hx-get" in content


def test_make_crud_genere_hx_post_pour_suppression():
    """make_crud génère hx-post pour la suppression (pas hx-delete, compatibilité max)."""
    content = (ROOT / "forge_cli" / "entities" / "make_crud.py").read_text(encoding="utf-8")
    assert "hx-post" in content
    assert "hx-delete" not in content


def test_make_crud_genere_hx_target():
    """make_crud génère hx-target pour cibler les résultats HTMX."""
    content = (ROOT / "forge_cli" / "entities" / "make_crud.py").read_text(encoding="utf-8")
    assert "hx-target" in content


# ── i18n dans les templates ───────────────────────────────────────────────────

def test_jinja_env_expose_trans():
    """Le renderer Jinja2 expose la fonction trans() globalement dans les templates."""
    content = (ROOT / "integrations" / "jinja2" / "renderer.py").read_text(encoding="utf-8")
    assert "trans" in content


def test_generateurs_publics_utilisent_trans():
    """Les générateurs de pages publiques utilisent trans() dans les templates générés."""
    for fname in ("public_page.py", "public_form.py", "public_list.py", "public_contact.py"):
        content = (ROOT / "forge_cli" / fname).read_text(encoding="utf-8")
        assert "trans(" in content, f"trans() absent dans {fname}"


# ── Absence de dépendances SPA ────────────────────────────────────────────────

def test_forge_cli_ne_contient_pas_react():
    """forge_cli/ ne contient aucune référence à React."""
    for f in (ROOT / "forge_cli").rglob("*.py"):
        content = f.read_text(encoding="utf-8")
        assert "import React" not in content
        assert "from React" not in content


def test_package_json_ne_contient_pas_webpack_ni_vite():
    """package.json ne déclare pas de bundler lourd (webpack, vite)."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    assert "webpack" not in all_deps
    assert "vite" not in all_deps


def test_doc_front_ne_promet_pas_spa():
    """docs/features/front.md ne transforme pas Forge en SPA."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "sans SPA" in content or "sans SPA" in content or "pas de SPA" in content or "ne transforme pas" in content


# ── Cohérence documentaire ────────────────────────────────────────────────────

def test_doc_front_md_existe():
    """docs/features/front.md existe."""
    assert (ROOT / "docs" / "features" / "front.md").exists()


def test_doc_front_mentionne_tailwind():
    """docs/features/front.md documente Tailwind."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "tailwind" in content.lower()


def test_doc_front_mentionne_htmx():
    """docs/features/front.md documente HTMX."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "HTMX" in content or "htmx" in content


def test_doc_front_mentionne_alpine():
    """docs/features/front.md documente Alpine.js."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "Alpine" in content


def test_doc_front_mentionne_js_init():
    """docs/features/front.md documente la commande forge js:init."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "js:init" in content


def test_doc_front_mentionne_bloc_scripts():
    """docs/features/front.md documente le bloc {% block scripts %}."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "block scripts" in content


def test_doc_front_mentionne_build_css():
    """docs/features/front.md documente la recompilation du CSS."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "build:css" in content or "npm" in content


# ── Séparation Forge Design ────────────────────────────────────────────────────

def test_front_py_ne_depend_pas_forge_design():
    """forge_cli/front.py ne référence pas Forge Design."""
    content = (ROOT / "forge_cli" / "front.py").read_text(encoding="utf-8")
    assert "forge-design" not in content.lower()
    assert "forge design" not in content.lower()


def test_doc_front_ne_promet_pas_editeur_graphique():
    """docs/features/front.md ne promet pas un éditeur graphique."""
    content = (ROOT / "docs" / "features" / "front.md").read_text(encoding="utf-8")
    assert "éditeur graphique" not in content.lower()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été modifié."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()


# ── Document d'audit et roadmap ───────────────────────────────────────────────

def test_audit_consolidation_front_001_existe():
    """docs/history/audits/consolidation-front-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").exists()


def test_audit_mentionne_tailwind():
    """Le document d'audit mentionne Tailwind."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").read_text(encoding="utf-8")
    assert "tailwind" in content.lower() or "Tailwind" in content


def test_audit_mentionne_htmx():
    """Le document d'audit mentionne HTMX."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").read_text(encoding="utf-8")
    assert "HTMX" in content or "htmx" in content


def test_audit_mentionne_alpine():
    """Le document d'audit mentionne Alpine."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").read_text(encoding="utf-8")
    assert "Alpine" in content


def test_audit_mentionne_block_scripts():
    """Le document d'audit mentionne le bloc scripts."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").read_text(encoding="utf-8")
    assert "scripts" in content


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-front-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_roadmap_marque_consolidation_front_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-FRONT-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-FRONT-001" in content
    assert "terminé" in content


def test_roadmap_priorite_est_dans_phase_consolidation():
    """La prochaine priorité immédiate est un ticket CONSOLIDATION-*."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert "CONSOLIDATION-" in bloc or "PUBLICATION-" in bloc or "POST-2.0-" in bloc or "DEPENDENCY-" in bloc or "RELEASE-" in bloc or "CMD-" in bloc or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc


def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()
