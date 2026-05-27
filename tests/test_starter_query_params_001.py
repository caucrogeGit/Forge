"""Garde-fou STARTER-QUERY-PARAMS-001.

Contrat public du starter 8 — Paramètres d'URL (palier 2 de la
progression officielle) :

- enregistré avec id "query-params" et number 8 ;
- aliases (`query-params`, `query_params`, `params`, `8`) ;
- kind "skeleton", requires_db False ;
- exactement 2 routes dans le snippet (index + hello) ;
- contrôleur livré avec exactement deux méthodes typées
  `request: Request -> Response` ;
- aucune vue HTML — `index` et `hello` retournent `Response.text(...)` ;
- `hello` utilise `request.param("name", default="Forge")` et
  retourne `Bonjour {name}` ;
- aucun fichier SQL, migration, entité ;
- --dry-run fonctionnel.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_cli.starters import cmd_starter_build
from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data" / "query-params"
FILES_DIR = STARTER_DIR / "files"
CONTROLLER = FILES_DIR / "mvc" / "controllers" / "query_params_controller.py"


# ── Métadonnées (starter.json + resolve) ──────────────────────────────────────


class TestQueryParamsStarterMetadata:

    def test_starter_json_existe(self):
        assert (STARTER_DIR / "starter.json").exists()

    def test_id_est_query_params(self):
        assert resolve("query-params")["id"] == "query-params"

    def test_number_est_8(self):
        assert resolve("query-params")["number"] == 8

    def test_kind_est_skeleton(self):
        assert resolve("query-params")["kind"] == "skeleton"

    def test_requires_db_est_false(self):
        assert resolve("query-params").get("requires_db") is False

    def test_status_est_available(self):
        assert resolve("query-params").get("status") == "available"

    @pytest.mark.parametrize("alias", ["query_params", "params", "8"])
    def test_resolvable_par_alias(self, alias: str):
        assert resolve(alias)["id"] == "query-params"

    def test_has_doc_url(self):
        assert resolve("query-params").get("doc_url")

    def test_has_home_route(self):
        assert resolve("query-params").get("home_route") == "/query-params"

    def test_name_public(self):
        assert resolve("query-params").get("name") == "Paramètres d'URL"


# ── Snippet de routes ─────────────────────────────────────────────────────────


class TestQueryParamsStarterRoutes:

    def test_snippet_existe(self):
        assert (STARTER_DIR / "routes.py.snippet").exists()

    def test_exactement_deux_routes(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        parsed = routes_from_snippet(snippet)
        assert len(parsed) == 2, (
            f"Attendu 2 routes dans le snippet query-params, trouvé "
            f"{len(parsed)} : {parsed}"
        )

    def test_routes_index_et_hello_presentes(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        paths = {path for _method, path in routes_from_snippet(snippet)}
        assert paths == {"/query-params", "/query-params/hello"}

    def test_marqueurs_forge_starter_presents(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "# forge-starter:query-params:start" in snippet
        assert "# forge-starter:query-params:end" in snippet

    def test_query_params_controller_importe_dans_snippet(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "QueryParamsController" in snippet

    def test_route_index_porte_le_nom_query_params_index(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert 'name="query_params_index"' in snippet

    def test_route_hello_porte_le_nom_query_params_hello(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert 'name="query_params_hello"' in snippet


# ── Contrôleur ─────────────────────────────────────────────────────────────────


class TestQueryParamsStarterController:

    def test_controller_existe(self):
        assert CONTROLLER.exists()

    def test_controller_importe_request(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert "from core.http.request import Request" in content

    def test_controller_importe_response(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert "from core.http.response import Response" in content

    def test_controller_importe_base_controller(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert "BaseController" in content
        assert "from core.mvc.controller.base_controller import BaseController" in content

    def test_classe_query_params_controller_presente(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert "class QueryParamsController(BaseController):" in content

    @pytest.mark.parametrize("method", ["index", "hello"])
    def test_methode_typee_presente(self, method: str):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert f"def {method}(request: Request) -> Response:" in content, (
            f"La méthode `{method}` doit être typée "
            "`request: Request -> Response`."
        )

    def test_index_retourne_response_text(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        # index doit retourner Response.text(...) avec un message d'aide
        assert "Response.text(" in content
        # le message d'aide doit guider l'utilisateur vers /hello
        assert "/query-params/hello" in content

    def test_hello_utilise_request_param_avec_default_forge(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert 'request.param("name", default="Forge")' in content

    def test_hello_retourne_bonjour_name(self):
        content = CONTROLLER.read_text(encoding="utf-8")
        assert 'f"Bonjour {name}"' in content

    def test_controller_ne_reference_pas_sql(self):
        content = CONTROLLER.read_text(encoding="utf-8").lower()
        assert "from mvc.models" not in content
        assert "import mariadb" not in content
        assert "from core.db" not in content


# ── Aucune vue HTML, aucune entité, aucun SQL ─────────────────────────────────


class TestQueryParamsStarterFilesScope:

    def test_aucun_dossier_views(self):
        path = FILES_DIR / "mvc" / "views"
        assert not path.exists(), (
            "Le starter query-params ne doit pas livrer de vues HTML."
        )

    def test_aucun_dossier_models(self):
        path = FILES_DIR / "mvc" / "models"
        assert not path.exists(), (
            "Le starter query-params ne doit pas livrer d'entités."
        )

    def test_aucun_fichier_sql(self):
        sql_files = list(FILES_DIR.rglob("*.sql"))
        assert not sql_files, (
            f"Le starter query-params ne doit livrer aucun .sql, trouvé : {sql_files}"
        )

    def test_aucun_dossier_migrations(self):
        for candidate in ("migrations", "db", "schema"):
            path = FILES_DIR / candidate
            assert not path.exists(), (
                f"Le starter query-params ne doit pas livrer `{candidate}/`."
            )

    def test_aucun_template_jinja(self):
        html_files = list(FILES_DIR.rglob("*.html"))
        assert not html_files, (
            f"Le starter query-params ne doit livrer aucun .html, trouvé : {html_files}"
        )


# ── Dry-run ───────────────────────────────────────────────────────────────────


class TestQueryParamsStarterDryRun:
    """forge starter:build 8 --dry-run s'exécute sans erreur."""

    def test_dry_run_fonctionne(self, capsys):
        cmd_starter_build(["8", "--dry-run"])
        output = capsys.readouterr().out
        assert "query-params" in output.lower() or "query_params" in output.lower()

    def test_dry_run_affiche_les_deux_routes(self, capsys):
        cmd_starter_build(["8", "--dry-run"])
        output = capsys.readouterr().out
        assert "/query-params" in output
        assert "/query-params/hello" in output

    def test_dry_run_n_implique_pas_db(self, capsys):
        # Le starter est requires_db: false donc le dry-run ne doit pas
        # mentionner d'opération DB
        cmd_starter_build(["8", "--dry-run"])
        output = capsys.readouterr().out.lower()
        # Pas de migration / db:init mentionnés
        assert "migration" not in output
        assert "db:init" not in output
