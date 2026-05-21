"""Garde-fou STARTER-WELCOME-001.

Contrat public du starter 7 — Bienvenue dans Forge :
- registered avec id "welcome" et number 7 ;
- kind "skeleton", requires_db false ;
- 6 routes dans le snippet ;
- fichiers contrôleur et vues présents ;
- doc présente ;
- --dry-run fonctionnel.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters import cmd_starter_build
from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "welcome"
FILES_DIR = STARTER_DIR / "files"
DOC_DIR = PROJECT_ROOT / "docs" / "starters" / "welcome"


class TestWelcomeStarterMetadata:
    """Le starter welcome est correctement enregistré."""

    def test_starter_json_existe(self):
        assert (STARTER_DIR / "starter.json").exists()

    def test_id_est_welcome(self):
        meta = resolve("welcome")
        assert meta["id"] == "welcome"

    def test_number_est_7(self):
        meta = resolve("welcome")
        assert meta["number"] == 7

    def test_kind_est_skeleton(self):
        meta = resolve("welcome")
        assert meta["kind"] == "skeleton"

    def test_requires_db_est_false(self):
        meta = resolve("welcome")
        assert meta.get("requires_db") is False

    def test_status_est_available(self):
        meta = resolve("welcome")
        assert meta.get("status") == "available"

    def test_resolvable_par_alias_bienvenue(self):
        meta = resolve("bienvenue")
        assert meta["id"] == "welcome"

    def test_has_doc_url(self):
        meta = resolve("welcome")
        assert meta.get("doc_url"), "doc_url absent pour le starter welcome"

    def test_has_home_route(self):
        meta = resolve("welcome")
        assert meta.get("home_route") == "/welcome"


class TestWelcomeStarterRoutes:
    """Le snippet contient exactement 6 routes sous /welcome."""

    def test_snippet_existe(self):
        assert (STARTER_DIR / "routes.py.snippet").exists()

    def test_six_routes_dans_snippet(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        parsed = routes_from_snippet(snippet)
        assert len(parsed) == 6, (
            f"Attendu 6 routes dans le snippet welcome, trouvé {len(parsed)} : {parsed}"
        )

    def test_routes_sous_welcome(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        for method, path in routes_from_snippet(snippet):
            assert path.startswith("/welcome"), (
                f"Route {method} {path} ne commence pas par /welcome"
            )

    def test_marqueurs_forge_starter_presents(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "# forge-starter:welcome:start" in snippet
        assert "# forge-starter:welcome:end" in snippet

    def test_welcome_controller_importe_dans_snippet(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "WelcomeController" in snippet


class TestWelcomeStarterFiles:
    """Les fichiers du starter welcome sont présents."""

    def test_controller_existe(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        assert ctrl.exists(), "welcome_controller.py absent du starter"

    def test_controller_importe_base_controller(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert "BaseController" in content

    def test_controller_a_six_methodes(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        methodes = ["index", "cycle", "request_example", "response_example",
                    "routing_example", "not_found_demo"]
        for m in methodes:
            assert f"def {m}(" in content, f"Méthode {m} absente de WelcomeController"

    @pytest.mark.parametrize("view", [
        "index.html",
        "cycle.html",
        "request_example.html",
        "response_example.html",
        "routing_example.html",
        "not_found_demo.html",
    ])
    def test_vue_presente(self, view: str):
        path = FILES_DIR / "mvc" / "views" / "welcome" / view
        assert path.exists(), f"Vue {view} absente du starter welcome"

    def test_controller_ne_reference_pas_sql(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8").lower()
        assert "from mvc.models" not in content
        assert "import mariadb" not in content


class TestWelcomeStarterDoc:
    """La documentation du starter welcome est présente."""

    def test_doc_dir_existe(self):
        assert DOC_DIR.is_dir(), "docs/starters/welcome/ doit exister"

    def test_index_md_existe(self):
        assert (DOC_DIR / "index.md").exists()

    def test_index_md_mentionne_starter_7(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Starter 7" in content

    def test_index_md_mentionne_forge_new_starter(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "--starter welcome" in content

    def test_index_md_mentionne_6_routes(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "6 routes" in content or "/welcome" in content


class TestWelcomeStarterDocNavigation:
    """Le starter welcome est intégré dans la navigation MkDocs et la page générale des starters."""

    def test_mkdocs_yml_reference_welcome(self):
        content = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "starters/welcome/index.md" in content, (
            "mkdocs.yml doit référencer starters/welcome/index.md dans la navigation"
        )

    def test_starters_index_mentionne_bienvenue(self):
        content = (PROJECT_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "Bienvenue" in content, (
            "docs/starters/index.md doit mentionner 'Bienvenue dans Forge'"
        )

    def test_starters_index_mentionne_lien_welcome(self):
        content = (PROJECT_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "welcome/" in content, (
            "docs/starters/index.md doit contenir un lien vers welcome/"
        )

    def test_starters_index_documente_commande_welcome(self):
        content = (PROJECT_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "--starter welcome" in content or "starter:build 7" in content, (
            "docs/starters/index.md doit documenter 'forge new --starter welcome' "
            "ou 'forge starter:build 7'"
        )

    def test_landing_pointe_vers_starters_welcome(self):
        landing = (PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html").read_text(
            encoding="utf-8"
        )
        assert "starters/welcome/" in landing, (
            "La landing doit contenir un lien vers starters/welcome/ "
            "(pas vers la page générale starters/)"
        )


class TestWelcomeStarterDryRun:
    """forge starter:build 7 --dry-run s'exécute sans erreur."""

    def test_dry_run_fonctionne(self, capsys):
        cmd_starter_build(["7", "--dry-run"])
        output = capsys.readouterr().out
        assert "welcome" in output.lower() or "bienvenue" in output.lower()

    def test_dry_run_affiche_6_routes(self, capsys):
        cmd_starter_build(["7", "--dry-run"])
        output = capsys.readouterr().out
        count = output.count("/welcome")
        assert count >= 6, (
            f"Le dry-run devrait afficher au moins 6 routes /welcome, trouvé {count}"
        )
