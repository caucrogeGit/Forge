"""Garde-fou STARTER-WELCOME-001 (refondu par STARTER-BONJOUR-FORGE-MINIMAL-001).

Contrat public du starter 7 — Bonjour Forge (version minimale) :

- registered avec id "welcome" et number 4 ;
- alias historiques (`welcome`, `bienvenue`, `7`) + nouveaux
  (`bonjour`, `bonjour-forge`) ;
- kind "skeleton", requires_db false ;
- exactement 1 route dans le snippet (`index`) — toutes les routes
  supplémentaires des versions précédentes (`/welcome/greet`, `/inspect`,
  `/cycle`, `/request`, `/response`, `/routing`, `/404-demo`) sont
  retirées ;
- contrôleur livré avec exactement une méthode typée
  `request: Request -> Response` ;
- aucune vue HTML — `index` retourne `Response.text(...)` ;
- doc présente, courte et alignée sur le contrat minimal ;
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
DOC_DIR = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "debutant"

_RETIRED_METHODS = (
    "greet",
    "inspect",
    "cycle",
    "request_example",
    "response_example",
    "routing_example",
    "not_found_demo",
)
_RETIRED_VIEWS = (
    "index.html",
    "cycle.html",
    "request_example.html",
    "response_example.html",
    "routing_example.html",
    "not_found_demo.html",
)


class TestWelcomeStarterMetadata:
    """Le starter welcome est correctement enregistré."""

    def test_starter_json_existe(self):
        assert (STARTER_DIR / "starter.json").exists()

    def test_id_est_welcome(self):
        assert resolve("welcome")["id"] == "welcome"

    def test_number_est_4(self):
        assert resolve("welcome")["number"] == 4

    def test_kind_est_skeleton(self):
        assert resolve("welcome")["kind"] == "skeleton"

    def test_requires_db_est_false(self):
        assert resolve("welcome").get("requires_db") is False

    def test_status_est_available(self):
        assert resolve("welcome").get("status") == "available"

    def test_resolvable_par_alias_bienvenue(self):
        assert resolve("bienvenue")["id"] == "welcome"

    def test_resolvable_par_alias_bonjour_forge(self):
        assert resolve("bonjour-forge")["id"] == "welcome"

    def test_has_doc_url(self):
        assert resolve("welcome").get("doc_url"), "doc_url absent pour le starter welcome"

    def test_has_home_route(self):
        assert resolve("welcome").get("home_route") == "/welcome"

    def test_name_public_bonjour_forge(self):
        assert resolve("welcome").get("name") == "Bonjour Forge"


class TestWelcomeStarterRoutes:
    """Le snippet contient exactement 1 route (STARTER-BONJOUR-FORGE-MINIMAL-001)."""

    def test_snippet_existe(self):
        assert (STARTER_DIR / "routes.py.snippet").exists()

    def test_exactement_une_route(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        parsed = routes_from_snippet(snippet)
        assert len(parsed) == 1, (
            f"Attendu 1 route dans le snippet welcome minimal, trouvé {len(parsed)} : {parsed}"
        )

    def test_route_index_presente(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        paths = {path for _method, path in routes_from_snippet(snippet)}
        assert paths == {"/welcome"}

    def test_aucune_route_retiree(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        for retired in ("/welcome/inspect", "/welcome/cycle", "/welcome/request",
                        "/welcome/response", "/welcome/routing", "/welcome/404-demo"):
            assert retired not in snippet, (
                f"Le snippet ne doit plus contenir la route {retired}"
            )

    def test_marqueurs_forge_starter_presents(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "# forge-starter:welcome:start" in snippet
        assert "# forge-starter:welcome:end" in snippet

    def test_welcome_controller_importe_dans_snippet(self):
        snippet = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "WelcomeController" in snippet


class TestWelcomeStarterFiles:
    """Le starter livre uniquement le contrôleur — aucune vue HTML."""

    def test_controller_existe(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        assert ctrl.exists()

    def test_controller_importe_request_et_response(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert "from core.http.request import Request" in content
        assert "from core.http.response import Response" in content

    def test_controller_importe_base_controller(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        assert "BaseController" in ctrl.read_text(encoding="utf-8")

    @pytest.mark.parametrize("method", ["index"])
    def test_methode_presente(self, method: str):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert f"def {method}(request: Request) -> Response:" in content

    @pytest.mark.parametrize("method", _RETIRED_METHODS)
    def test_methode_retiree_absente(self, method: str):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8")
        assert f"def {method}(" not in content, (
            f"La méthode `{method}` doit être retirée du contrôleur minimal."
        )

    def test_index_utilise_response_text(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        assert 'Response.text("Bonjour Forge")' in ctrl.read_text(encoding="utf-8")

    def test_controleur_ne_lit_aucun_parametre_url(self):
        # Palier 1 = une seule responsabilité : request.param appartient au
        # palier 2 (query-params).
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        assert "request.param" not in ctrl.read_text(encoding="utf-8")

    def test_dossier_views_welcome_absent(self):
        path = FILES_DIR / "mvc" / "views" / "welcome"
        assert not path.exists(), (
            "Le dossier `mvc/views/welcome/` doit être retiré "
            "(STARTER-BONJOUR-FORGE-MINIMAL-001)."
        )

    @pytest.mark.parametrize("view", _RETIRED_VIEWS)
    def test_vue_retiree_absente(self, view: str):
        path = FILES_DIR / "mvc" / "views" / "welcome" / view
        assert not path.exists(), (
            f"La vue `{view}` doit être retirée du starter minimal."
        )

    def test_controller_ne_reference_pas_sql(self):
        ctrl = FILES_DIR / "mvc" / "controllers" / "welcome_controller.py"
        content = ctrl.read_text(encoding="utf-8").lower()
        assert "from mvc.models" not in content
        assert "import mariadb" not in content


class TestWelcomeStarterDoc:
    """La documentation du starter est présente, courte et alignée."""

    def test_doc_dir_existe(self):
        assert DOC_DIR.is_dir()

    def test_index_md_existe(self):
        assert (DOC_DIR / "welcome.md").exists()

    def test_index_md_titre_est_bonjour_forge(self):
        content = (DOC_DIR / "welcome.md").read_text(encoding="utf-8")
        assert content.startswith("# Bonjour Forge")

    # Assertions retirées par STARTER-SEQUENTIAL-NAV-001 :
    # « Starter 7 » et « --starter welcome » sont désormais INTERDITS
    # dans les pages pédagogiques de starters (la page suppose que
    # l'utilisateur est déjà dans un projet créé avec ce starter ; les
    # numéros internes restent confinés à starter.json + tests
    # techniques). Voir tests/meta/test_starter_sequential_nav_001.py
    # qui assert l'ABSENCE de ces patterns sur toutes les pages
    # docs/starters/*/index.md.

    def test_index_md_documente_la_route(self):
        content = (DOC_DIR / "welcome.md").read_text(encoding="utf-8")
        assert "/welcome" in content
        assert "/welcome/greet" not in content, (
            "Palier 1 ne doit plus documenter /welcome/greet — la lecture "
            "d'un paramètre d'URL est la responsabilité du palier query-params."
        )

    def test_index_md_documente_response_text(self):
        content = (DOC_DIR / "welcome.md").read_text(encoding="utf-8")
        assert 'Response.text("Bonjour Forge")' in content

    def test_index_md_courte(self):
        """La doc minimale tient en moins de 150 lignes (objectif ~80-120)."""
        lines = (DOC_DIR / "welcome.md").read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 150, (
            f"La doc starter minimal doit rester courte ; {len(lines)} lignes trouvées."
        )

    @pytest.mark.parametrize("noise", [
        "mermaid",
        "Tailwind",
        "tailwind.css",
        "Symfony",
        "Django",
        "Response.debug",
        "BaseController.render",
        "404",
    ])
    def test_index_md_ne_contient_pas_les_notions_repoussees(self, noise: str):
        """Notions volontairement repoussées à de futurs starters dédiés."""
        content = (DOC_DIR / "welcome.md").read_text(encoding="utf-8")
        assert noise not in content, (
            f"`{noise}` ne doit pas apparaître dans le starter minimal "
            "(repoussé à un futur starter dédié)."
        )


class TestWelcomeStarterDocNavigation:
    """Le starter welcome reste intégré dans la navigation MkDocs."""

    def test_mkdocs_yml_reference_welcome(self):
        content = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "starters/welcome-forge/debutant/welcome.md" in content

    def test_starters_index_mentionne_bonjour_forge(self):
        content = (PROJECT_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "Bonjour Forge" in content


class TestWelcomeStarterDryRun:
    """forge starter:build 7 --dry-run s'exécute sans erreur."""

    def test_dry_run_fonctionne(self, capsys):
        cmd_starter_build(["4", "--dry-run"])
        output = capsys.readouterr().out
        assert "welcome" in output.lower() or "bienvenue" in output.lower()

    def test_dry_run_affiche_la_route(self, capsys):
        # welcome = une seule route (palier 1, une responsabilité).
        cmd_starter_build(["4", "--dry-run"])
        output = capsys.readouterr().out
        assert "/welcome" in output
        assert "/welcome/greet" not in output
