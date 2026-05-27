"""Garde-fou STARTER-WELCOME-001 (refondu par STARTER-BONJOUR-FORGE-001).

Contrat public du starter 7 — Bonjour Forge :
- registered avec id "welcome" et number 7 ;
- alias historiques (`welcome`, `bienvenue`, `7`) + nouveaux
  (`bonjour`, `bonjour-forge`) ;
- kind "skeleton", requires_db false ;
- 8 routes dans le snippet (index/greet/inspect en `Response.text/debug`
  + cycle/request/response/routing/404-demo qui rendent un template) ;
- contrôleur + 5 vues HTML présentes ;
- doc présente et repositionnée autour de « Bonjour Forge » ;
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
    """Le snippet contient les 8 routes sous /welcome (STARTER-BONJOUR-FORGE-001).

    Ajout de `/welcome/greet` (`Response.text` + `request.param`) et
    `/welcome/inspect` (`Response.debug(request.data)`) en plus des 6
    routes historiques.
    """

    def test_snippet_existe(self):
        assert (STARTER_DIR / "routes.py.snippet").exists()

    def test_huit_routes_dans_snippet(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        parsed = routes_from_snippet(snippet)
        assert len(parsed) == 8, (
            f"Attendu 8 routes dans le snippet welcome, trouvé {len(parsed)} : {parsed}"
        )

    def test_routes_greet_et_inspect_presentes(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        paths = {path for _method, path in routes_from_snippet(snippet)}
        assert "/welcome/greet" in paths
        assert "/welcome/inspect" in paths

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

    def test_controller_a_huit_methodes(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        methodes = ["index", "greet", "inspect",
                    "cycle", "request_example", "response_example",
                    "routing_example", "not_found_demo"]
        for m in methodes:
            assert f"def {m}(" in content, f"Méthode {m} absente de WelcomeController"

    def test_index_utilise_response_text(self):
        """STARTER-BONJOUR-FORGE-001 : `index` retourne `Response.text("Bonjour Forge")`."""
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert 'Response.text("Bonjour Forge")' in content, (
            "WelcomeController.index doit utiliser Response.text(\"Bonjour Forge\")"
        )

    def test_greet_utilise_request_param(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert 'request.param("name"' in content, (
            "WelcomeController.greet doit montrer request.param(\"name\", default=...)"
        )

    def test_inspect_utilise_response_debug(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert "Response.debug(request.data)" in content, (
            "WelcomeController.inspect doit utiliser Response.debug(request.data)"
        )

    @pytest.mark.parametrize("view", [
        "cycle.html",
        "request_example.html",
        "response_example.html",
        "routing_example.html",
        "not_found_demo.html",
    ])
    def test_vue_presente(self, view: str):
        path = FILES_DIR / "mvc" / "views" / "welcome" / view
        assert path.exists(), f"Vue {view} absente du starter welcome"

    def test_vue_welcome_index_html_retiree(self):
        """STARTER-BONJOUR-FORGE-001 : la vue `welcome/index.html` a été
        retirée — `index` retourne `Response.text("Bonjour Forge")` sans
        template."""
        path = FILES_DIR / "mvc" / "views" / "welcome" / "index.html"
        assert not path.exists(), (
            "welcome/index.html doit être retirée (Response.text remplace le rendu)"
        )

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
        assert "Starter 7" in content, "Starter 7 doit rester présent comme référence technique"

    def test_index_md_mentionne_premier_pas(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Premier pas" in content, (
            "La doc doit continuer à mentionner 'Premier pas' "
            "(sous-titre ou rappel pour ne pas casser la pédagogie historique)"
        )

    def test_index_md_titre_est_bonjour_forge(self):
        """STARTER-BONJOUR-FORGE-001 : le titre H1 est désormais 'Bonjour Forge'."""
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert content.startswith("# Bonjour Forge"), (
            "Le titre H1 de la page doit être '# Bonjour Forge'"
        )

    def test_index_md_mentionne_forge_new_starter(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "--starter welcome" in content

    def test_index_md_mentionne_6_routes(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "6 routes" in content or "/welcome" in content


class TestWelcomeStarterView:
    """Le starter welcome documente explicitement la couche View (STARTER-WELCOME-VIEW-001)."""

    def test_cycle_html_nomme_view(self):
        cycle = (FILES_DIR / "mvc" / "views" / "welcome" / "cycle.html").read_text(encoding="utf-8")
        assert "View" in cycle, "cycle.html doit nommer la couche View explicitement"

    def test_cycle_html_documente_cycle_html_complet(self):
        cycle = (FILES_DIR / "mvc" / "views" / "welcome" / "cycle.html").read_text(encoding="utf-8")
        assert "Response HTML" in cycle, (
            "cycle.html doit documenter le cycle HTML complet avec 'Response HTML'"
        )

    def test_cycle_html_documente_cycle_json(self):
        cycle = (FILES_DIR / "mvc" / "views" / "welcome" / "cycle.html").read_text(encoding="utf-8")
        assert "Response JSON" in cycle, (
            "cycle.html doit documenter le cycle JSON séparé avec 'Response JSON'"
        )

    def test_doc_presente_les_deux_cycles_html_et_json(self):
        """STARTER-BONJOUR-FORGE-001 : la vue `index.html` a été retirée ;
        c'est désormais la doc qui présente les deux cycles HTML/JSON."""
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "View" in content, "La doc doit mentionner la couche View"
        assert "Response JSON" in content, "La doc doit mentionner le cycle JSON"

    def test_response_example_distingue_html_et_json(self):
        resp = (FILES_DIR / "mvc" / "views" / "welcome" / "response_example.html").read_text(
            encoding="utf-8"
        )
        assert "View" in resp, "response_example.html doit mentionner la couche View"
        assert "sans View" in resp or "Response JSON" in resp, (
            "response_example.html doit préciser que JSON ne passe pas par une View"
        )

    def test_doc_mentionne_view(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "View" in content, "La doc du starter doit mentionner la couche View"

    def test_doc_mentionne_cycle_html_avec_view(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert 'View HTML' in content, (
            "La doc doit représenter la View dans le cycle HTML (Mermaid 'View HTML')"
        )
        assert '!!! success "Cycle HTML — page rendue au navigateur"' in content, (
            "La doc doit confirmer le cycle HTML via l'encadré success"
        )

    def test_doc_mentionne_cycle_json_sans_view(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Response JSON" in content, (
            "La doc doit mentionner le cycle JSON avec 'Response JSON'"
        )

    def test_pas_de_sql_dans_les_vues_welcome(self):
        # `index.html` retirée par STARTER-BONJOUR-FORGE-001.
        for view in ["cycle.html", "response_example.html", "routing_example.html"]:
            content = (FILES_DIR / "mvc" / "views" / "welcome" / view).read_text(
                encoding="utf-8"
            )
            assert "import mariadb" not in content, f"{view} ne doit pas importer mariadb"
            assert "SELECT " not in content and "INSERT " not in content, (
                f"{view} ne doit pas contenir de requêtes SQL"
            )


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

    def test_starters_index_mentionne_bonjour_forge(self):
        content = (PROJECT_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "Bonjour Forge" in content, (
            "docs/starters/index.md doit afficher 'Bonjour Forge' "
            "comme libellé public du starter welcome (STARTER-BONJOUR-FORGE-001)"
        )

    def test_landing_pointe_vers_starters_welcome(self):
        landing = (PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html").read_text(
            encoding="utf-8"
        )
        assert "starters/welcome/" in landing, (
            "La landing doit contenir un lien vers starters/welcome/ "
            "(pas vers la page générale starters/)"
        )


class TestWelcomeStarterDocPedagogy:
    """La documentation welcome est pédagogique et détaillée (DOC-PREMIER-PAS-PEDAGOGY-001)."""

    def test_doc_contient_code_complet_genere(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Le code complet généré par ce starter" in content
        assert "### 1. Les routes complètes" in content
        assert "### 2. Le contrôleur complet" in content
        # 5 vues HTML désormais (STARTER-BONJOUR-FORGE-001).
        assert "### 3. Les 5 vues HTML" in content

    def test_doc_contient_chemins_code_reel(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        # Note : `mvc/views/welcome/index.html` n'est plus dans la liste
        # (STARTER-BONJOUR-FORGE-001 — la vue a été retirée). Sa mention
        # textuelle dans la doc (note explicative) reste tolérée.
        expected_paths = [
            "mvc/routes.py",
            "mvc/controllers/welcome_controller.py",
            "mvc/views/welcome/cycle.html",
            "mvc/views/welcome/request_example.html",
            "mvc/views/welcome/response_example.html",
            "mvc/views/welcome/routing_example.html",
            "mvc/views/welcome/not_found_demo.html",
        ]
        for path in expected_paths:
            assert path in content, f"{path} doit apparaître dans la doc welcome"

    def test_doc_contient_routes_reelles_completes(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        expected_routes = [
            'pub.add("GET", "/welcome",           WelcomeController.index',
            'pub.add("GET", "/welcome/greet",     WelcomeController.greet',
            'pub.add("GET", "/welcome/inspect",   WelcomeController.inspect',
            'pub.add("GET", "/welcome/cycle",     WelcomeController.cycle',
            'pub.add("GET", "/welcome/request",   WelcomeController.request_example',
            'pub.add("GET", "/welcome/response",  WelcomeController.response_example',
            'pub.add("GET", "/welcome/routing",   WelcomeController.routing_example',
            'pub.add("GET", "/welcome/404-demo",  WelcomeController.not_found_demo',
        ]
        for route in expected_routes:
            assert route in content, f"Route réelle absente de la doc : {route}"

    def test_doc_contient_controller_reel_complet(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        expected_methods = [
            "def index(request: Request) -> Response:",
            "def greet(request: Request) -> Response:",
            "def inspect(request: Request) -> Response:",
            "def cycle(request: Request) -> Response:",
            "def request_example(request: Request) -> Response:",
            "def response_example(request: Request) -> Response:",
            "def routing_example(request: Request) -> Response:",
            "def not_found_demo(request: Request) -> Response:",
        ]
        assert "class WelcomeController(BaseController):" in content
        for method in expected_methods:
            assert method in content, f"Méthode réelle absente de la doc : {method}"

    def test_doc_titre_public(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Bonjour Forge" in content, (
            "La doc doit conserver le libellé public 'Bonjour Forge' "
            "(STARTER-BONJOUR-FORGE-001)"
        )

    def test_doc_ne_contient_plus_bloc_html_orange(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "border:1px solid #FED7AA" not in content
        assert "linear-gradient" not in content

    def test_doc_place_cycles_avant_code_complet(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Les deux cycles HTTP Forge" in content
        assert "## Le code complet généré par ce starter" in content
        assert content.index("## Les deux cycles HTTP Forge") < content.index(
            "## Le code complet généré par ce starter"
        )

    def test_doc_contient_onglets_cycles_http(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '=== "Cycle HTML"' in content
        assert '=== "Cycle JSON"' in content

    def test_doc_contient_schemas_visuels_mermaid(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "```mermaid" in content
        assert content.count("flowchart") >= 3
        expected_terms = [
            "python app.py",
            "Application Forge démarrée",
            "GET /welcome",
            "WelcomeController.index(request)",
            "Response HTML",
            "Response JSON",
        ]
        for term in expected_terms:
            assert term in content, f"Terme absent des schémas visuels : {term}"

    def test_doc_contient_schema_route_controller_vue(self):
        """Schéma route→contrôleur→vue : pointé sur `/welcome/cycle` qui
        rend une vue (STARTER-BONJOUR-FORGE-001 — `/welcome` n'a plus de
        vue puisque `index` retourne `Response.text`)."""
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert 'A["GET /welcome/cycle"] --> B["mvc/routes.py"]' in content
        assert 'B --> C["pub.add(...)"]' in content
        assert 'D --> E["welcome/cycle.html"]' in content

    def test_doc_cycle_html_complet(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        idx_html = content.index('=== "Cycle HTML"')
        idx_json = content.index('=== "Cycle JSON"')
        tab_html = content[idx_html:idx_json]
        assert 'View HTML' in tab_html, (
            "Le cycle HTML doit représenter la View HTML dans le schéma Mermaid"
        )
        assert 'Response HTML' in tab_html, (
            "Le cycle HTML doit représenter Response HTML dans le schéma Mermaid"
        )

    def test_doc_cycle_json_complet(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Request → Router → Controller → Response JSON" in content, (
            "La doc doit présenter le cycle JSON complet : "
            "'Request → Router → Controller → Response JSON'"
        )

    def test_doc_explique_app_py(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Où intervient `app.py` ?" in content
        assert "python app.py" in content
        assert "Forge reçoit la requête HTTP transmise par le serveur de développement" in content

    def test_doc_clarifie_app_py_et_route_racine(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        expected_terms = [
            "`app.py` ne choisit pas la route `/`",
            "GET /",
            "Router cherche GET + /",
            "HomeController.index(request)",
            "app.py` démarre Forge",
            "Le navigateur demande une URL",
            "Le routeur choisit le contrôleur",
            "Le contrôleur produit la réponse",
        ]
        for term in expected_terms:
            assert term in content, f"Clarification app.py / route racine absente : {term}"

    def test_doc_ne_decrit_pas_app_py_comme_routeur(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        forbidden = [
            "app.py prend la route /",
            "app.py appelle /",
            "app.py affiche la page /",
            "app.py choisit la page d’accueil",
            "app.py choisit la page d'accueil",
        ]
        found = [needle for needle in forbidden if needle in content]
        assert not found, f"Formulation trompeuse sur app.py : {found}"

    def test_doc_explique_execution_controller(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Comment Forge exécute le contrôleur ?" in content
        assert "WelcomeController.index(request)" in content
        assert 'pub.add("GET", "/welcome", WelcomeController.index, name="welcome_index")' in content

    def test_doc_contient_onglets_frameworks_symfony_django(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Si vous venez d’un autre framework" in content
        assert '=== "Symfony"' in content
        assert '=== "Django"' in content
        assert '!!! info "Si vous venez de Symfony"' not in content
        assert "`WelcomeController` est la classe contrôleur" in content

    def test_doc_explique_vocabulaire_django_mtv(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        expected_terms = [
            "architecture MTV",
            "`Model`",
            "`Template`",
            "`View`",
            "`Controller`",
            "Django appelle souvent une `view`",
            "méthode de contrôleur",
            "route → contrôleur → vue",
            "WelcomeController.index(request)",
        ]
        for term in expected_terms:
            assert term in content, f"Repère Django/Forge absent : {term}"

    def test_doc_explique_request(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "request.method" in content or "request.path" in content, (
            "La doc doit expliquer l'objet Request avec ses attributs"
        )

    def test_doc_explique_router(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "mvc/routes.py" in content, (
            "La doc doit mentionner mvc/routes.py pour expliquer le Router"
        )

    def test_doc_explique_controller(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "BaseController.render" in content and "WelcomeController" in content, (
            "La doc doit expliquer le Controller avec l'API réelle du starter"
        )

    def test_doc_contient_table_url_methode_vue(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "| URL | Méthode appelée | Vue rendue |" in content
        # `/welcome`, `/welcome/greet` et `/welcome/inspect` n'ont pas de
        # vue : ils retournent `Response.text(...)` ou `Response.debug(...)`.
        expected_rows = [
            "| `/welcome` | `WelcomeController.index(request)` |",
            "| `/welcome/greet?name=…` | `WelcomeController.greet(request)` |",
            "| `/welcome/inspect` | `WelcomeController.inspect(request)` |",
            "| `/welcome/cycle` | `WelcomeController.cycle(request)` | `welcome/cycle.html` |",
            "| `/welcome/request` | `WelcomeController.request_example(request)` | `welcome/request_example.html` |",
            "| `/welcome/response` | `WelcomeController.response_example(request)` | `welcome/response_example.html` |",
            "| `/welcome/routing` | `WelcomeController.routing_example(request)` | `welcome/routing_example.html` |",
            "| `/welcome/404-demo` | `WelcomeController.not_found_demo(request)` | `welcome/not_found_demo.html` |",
        ]
        for row in expected_rows:
            assert row in content, f"Ligne table URL/méthode/vue absente : {row}"

    def test_doc_url_http_pas_https(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "http://localhost:8000/welcome" in content, (
            "La doc doit utiliser http:// et non https:// pour localhost"
        )

    def test_doc_pas_url_https_localhost(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "https://localhost:8000/welcome" not in content, (
            "La doc ne doit pas contenir https://localhost (le dev tourne en HTTP)"
        )

    def test_doc_contient_parcours_lecture(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "## Lire l’application dans le bon ordre" in content, (
            "La doc doit proposer un parcours de lecture directive"
        )
        assert "## Visite guidée en 10 minutes" not in content

    def test_doc_contient_limites(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "ne fait pas" in content or "ne fait **pas**" in content, (
            "La doc doit décrire ce que ce starter ne fait pas"
        )

    def test_doc_contient_structure_projet(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "├── routes.py" in content
        assert "controllers/" in content and "views/" in content, (
            "La doc doit présenter la structure du projet déployé"
        )

    def test_doc_clarifie_absence_route_json_reelle(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "n'expose pas de route JSON dédiée" in content, (
            "La doc doit clarifier que le starter explique JSON sans route JSON réelle"
        )

    def test_doc_ne_contient_pas_api_inventee(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        forbidden = ["self.render", "self.redirect", "router.get("]
        found = [needle for needle in forbidden if needle in content]
        assert not found, f"API approximative ou absente du starter documentée : {found}"

    def test_doc_ne_documente_pas_router_get(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "router.get(" not in content, (
            "La doc ne doit pas documenter router.get( si cette API n'existe pas "
            "dans le starter welcome"
        )

    def test_doc_preserve_message_sans_sql(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Sans SQL." in content
        assert "Sans base de données." in content
        assert "Sans entité." in content
        assert "Sans migration." in content
        assert "Sans CRUD." in content

    def test_doc_explique_vues_html_simples(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "vues sont volontairement des fichiers HTML complets" in content
        for marker in ["base.html", "include", "extends", "block"]:
            assert marker in content

    def test_doc_contient_bloc_a_retenir(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '!!! success "À retenir"' in content
        assert "Le Router choisit le Controller." in content
        assert "Le JSON peut être renvoyé sans View." in content

    def test_doc_liens_finaux_propres(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "[Starter 1 — Contacts](../01-contact-simple/)" in content
        assert "[Vue d'ensemble des starters](../)" in content
        assert "../01-contact-simple/index.md" not in content
        assert "../index.md" not in content


class TestWelcomeStarterDocCodeVisible:
    """Les vues du starter welcome sont visibles par défaut (DOC-PREMIER-PAS-CODE-VISIBLE-001)."""

    def test_pas_de_details_ferme_pour_les_vues(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "<details>\n<summary><code>mvc/views/welcome/" not in content, (
            "Les blocs <details> des vues ne doivent pas être fermés par défaut"
        )

    def test_details_open_pour_chaque_vue(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        # `welcome/index.html` n'est plus listée — la vue a été retirée
        # par STARTER-BONJOUR-FORGE-001.
        vues = [
            "mvc/views/welcome/cycle.html",
            "mvc/views/welcome/request_example.html",
            "mvc/views/welcome/response_example.html",
            "mvc/views/welcome/routing_example.html",
            "mvc/views/welcome/not_found_demo.html",
        ]
        for vue in vues:
            assert f"<details open>\n<summary><code>{vue}" in content, (
                f"La vue {vue} doit être dans un <details open> visible par défaut"
            )

    def test_doc_mentionne_classe_controleur_principale(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "classe contrôleur principale" in content, (
            "La doc doit mentionner qu'il y a une classe contrôleur principale"
        )

    def test_doc_mentionne_cinq_vues_html(self):
        """STARTER-BONJOUR-FORGE-001 : 5 vues HTML, plus 3 routes sans vue."""
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "cinq vues HTML" in content, (
            "La doc doit préciser que le starter contient cinq vues HTML "
            "(les trois routes /welcome, /welcome/greet et /welcome/inspect "
            "n'ont pas de vue)"
        )


class TestWelcomeStarterDocCycleTabs:
    """Les onglets Cycle HTML / Cycle JSON contiennent des schémas Mermaid (DOC-PREMIER-PAS-CYCLES-TABS-VISUAL-001)."""

    def test_onglet_cycle_html_present(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '=== "Cycle HTML"' in content, (
            'La doc doit contenir l\'onglet === "Cycle HTML"'
        )

    def test_onglet_cycle_json_present(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '=== "Cycle JSON"' in content, (
            'La doc doit contenir l\'onglet === "Cycle JSON"'
        )

    def test_cycle_html_contient_mermaid(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        idx_html = content.index('=== "Cycle HTML"')
        idx_json = content.index('=== "Cycle JSON"')
        tab_html = content[idx_html:idx_json]
        assert "```mermaid" in tab_html, (
            "L'onglet Cycle HTML doit contenir un schéma Mermaid"
        )
        assert "flowchart LR" in tab_html, (
            "L'onglet Cycle HTML doit utiliser flowchart LR"
        )
        assert 'View HTML' in tab_html, (
            "L'onglet Cycle HTML doit représenter la View HTML dans le schéma"
        )

    def test_cycle_json_contient_mermaid(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        idx_json = content.index('=== "Cycle JSON"')
        tab_json = content[idx_json:idx_json + 600]
        assert "```mermaid" in tab_json, (
            "L'onglet Cycle JSON doit contenir un schéma Mermaid"
        )
        assert "flowchart LR" in tab_json, (
            "L'onglet Cycle JSON doit utiliser flowchart LR"
        )

    def test_cycle_html_admonition_success(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '!!! success "Cycle HTML — page rendue au navigateur"' in content, (
            "L'onglet Cycle HTML doit contenir un encadré !!! success avec ce libellé"
        )

    def test_cycle_json_admonition_info(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '!!! info "Cycle JSON — données renvoyées directement"' in content, (
            "L'onglet Cycle JSON doit contenir un encadré !!! info avec ce libellé"
        )

    def test_pas_de_text_fence_dans_onglets(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert '    ```text\n    Request → Router → Controller → View → Response HTML' not in content, (
            "L'onglet Cycle HTML ne doit plus utiliser un bloc ```text simple"
        )
        assert '    ```text\n    Request → Router → Controller → Response JSON' not in content, (
            "L'onglet Cycle JSON ne doit plus utiliser un bloc ```text simple"
        )

    def test_schema_texte_redondant_app_py_supprime(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "navigateur → GET /welcome\n    ↓\nRequest" not in content, (
            "Le schéma texte redondant de la section app.py doit être supprimé"
        )

    def test_phrase_code_complet_correcte(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "Après ces repères, regardons maintenant le code complet généré par Forge" in content, (
            "La phrase doit être 'Après ces repères...' et non 'Avant d'expliquer...'"
        )
        assert "Avant d'expliquer les concepts, regardons d'abord ce que Forge génère réellement" not in content, (
            "L'ancienne phrase incohérente doit être supprimée"
        )

    def test_symfony_formulation_factuelle(self):
        content = (DOC_DIR / "index.md").read_text(encoding="utf-8")
        assert "sans annotation ni configuration cachée" not in content, (
            "La formulation polémique Symfony doit être remplacée"
        )
        assert "Dans ce starter Forge, le lien route → méthode est visible directement dans" in content, (
            "La formulation factuelle doit être présente"
        )


class TestWelcomeStarterDryRun:
    """forge starter:build 7 --dry-run s'exécute sans erreur."""

    def test_dry_run_fonctionne(self, capsys):
        cmd_starter_build(["7", "--dry-run"])
        output = capsys.readouterr().out
        assert "welcome" in output.lower() or "bienvenue" in output.lower()

    def test_dry_run_affiche_au_moins_huit_routes(self, capsys):
        """STARTER-BONJOUR-FORGE-001 : le starter expose désormais 8 routes
        (ajout de `/welcome/greet` et `/welcome/inspect`)."""
        cmd_starter_build(["7", "--dry-run"])
        output = capsys.readouterr().out
        count = output.count("/welcome")
        assert count >= 8, (
            f"Le dry-run devrait afficher au moins 8 routes /welcome, trouvé {count}"
        )
