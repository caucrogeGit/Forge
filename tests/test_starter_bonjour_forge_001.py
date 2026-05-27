"""Tests — STARTER-BONJOUR-FORGE-001.

Vérifie le contrat pédagogique du starter d'entrée refondu :

  1. Le starter est désormais nommé « Bonjour Forge ».
  2. Le contrôleur livré importe `Request` et `Response`.
  3. La méthode `index` est annotée `request: Request -> Response`.
  4. Le **premier** exemple utilise `Response.text("Bonjour Forge")` —
     aucune dépendance à un template au premier contact.
  5. `request.param("name", default="Forge")` est documenté.
  6. `Response.debug(request.data)` est documenté (dump HTML en dev).
  7. `BaseController.render(...)` reste documenté MAIS arrive APRÈS
     les exemples `Response.text` / `Response.debug` dans la doc.
  8. La progression pédagogique attendue est lisible dans le doc.
  9. Aucune référence cassée du nom historique : « Bienvenue » /
     « Premier pas » restent retrouvables pour les liens et les
     personnes habituées au précédent libellé.
 10. Les anciens alias (`welcome`, `bienvenue`, `7`) sont conservés ;
     les nouveaux (`bonjour`, `bonjour-forge`) sont ajoutés.

Les tests évitent toute exécution réelle du serveur HTTP : ils se
contentent d'exécuter les méthodes du contrôleur avec une `FakeRequest`
en mémoire.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from forge_cli.starters.registry import resolve
from tests.fake_request import FakeRequest


_REPO_ROOT = Path(__file__).resolve().parent.parent
_STARTER_DIR = _REPO_ROOT / "forge_cli" / "starters" / "data" / "welcome"
_CONTROLLER = _STARTER_DIR / "files" / "mvc" / "controllers" / "welcome_controller.py"
_STARTER_JSON = _STARTER_DIR / "starter.json"
_DOC = _REPO_ROOT / "docs" / "starters" / "welcome" / "index.md"


# ── 1. Renommage public ──────────────────────────────────────────────────────


class TestStarterRenamedToBonjourForge:
    def test_starter_json_name_est_bonjour_forge(self):
        meta = json.loads(_STARTER_JSON.read_text(encoding="utf-8"))
        assert meta["name"] == "Bonjour Forge", (
            f"starter.json.name doit être 'Bonjour Forge', "
            f"trouvé : {meta.get('name')!r}"
        )

    def test_doc_h1_est_bonjour_forge(self):
        content = _DOC.read_text(encoding="utf-8")
        first_line = content.splitlines()[0]
        assert first_line == "# Bonjour Forge", (
            f"H1 attendu : '# Bonjour Forge', trouvé : {first_line!r}"
        )

    def test_doc_garde_reference_premier_pas(self):
        """Pour ne pas casser la pédagogie historique, le terme 'Premier pas'
        doit rester findable dans la doc (sous-titre ou rappel)."""
        content = _DOC.read_text(encoding="utf-8")
        assert "Premier pas" in content

    def test_starters_index_mentionne_bonjour_forge(self):
        content = (_REPO_ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
        assert "Bonjour Forge" in content


# ── 2. Aliases conservés + nouveaux ──────────────────────────────────────────


class TestStarterAliases:
    @pytest.mark.parametrize("alias", ["welcome", "bienvenue", "7"])
    def test_aliases_historiques_resolvent(self, alias):
        meta = resolve(alias)
        assert meta["id"] == "welcome"

    @pytest.mark.parametrize("alias", ["bonjour", "bonjour-forge"])
    def test_nouveaux_aliases_resolvent(self, alias):
        meta = resolve(alias)
        assert meta["id"] == "welcome"


# ── 3. Contrôleur typé Request / Response ────────────────────────────────────


class TestControllerImports:
    def test_importe_request(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "from core.http.request import Request" in content

    def test_importe_response(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "from core.http.response import Response" in content

    def test_importe_base_controller(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "from core.mvc.controller.base_controller import BaseController" in content


class TestControllerSignatures:
    """Toutes les actions publiques sont typées `request: Request -> Response`."""

    @pytest.mark.parametrize("method", [
        "index", "greet", "inspect",
        "cycle", "request_example", "response_example",
        "routing_example", "not_found_demo",
    ])
    def test_signature_typee(self, method):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert f"def {method}(request: Request) -> Response:" in content, (
            f"{method} doit être annotée `request: Request -> Response`"
        )


# ── 4. Premier exemple : Response.text("Bonjour Forge") ──────────────────────


class TestFirstStepIsResponseText:
    """STARTER-BONJOUR-FORGE-001 : `/welcome` répond sans template.

    L'exécution du contrôleur ne doit JAMAIS appeler `BaseController.render`
    pour `index` — seulement `Response.text("Bonjour Forge")`.
    """

    def _load_controller_module(self):
        """Charge le module contrôleur sans dépendre du projet réel."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_welcome_controller_under_test", _CONTROLLER,
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_index_appelle_response_text_bonjour_forge(self):
        module = self._load_controller_module()
        request = FakeRequest("GET", "/welcome")
        response = module.WelcomeController.index(request)
        assert response.status == 200
        assert response.content_type == "text/plain; charset=utf-8"
        assert response.body == b"Bonjour Forge"

    def test_index_n_ouvre_aucun_template(self, monkeypatch):
        """Le starter doit pouvoir répondre 'Bonjour Forge' SANS template.

        On vérifie qu'aucun appel à `template_manager.render` n'est émis
        par `index`. Cela garantit que la route entry est sans dépendance
        au moteur de template.
        """
        module = self._load_controller_module()
        calls: list[tuple[str, dict]] = []

        # Substitue render() sur la classe utilisée par le contrôleur.
        def _trapping_render(self, template, ctx):  # noqa: ANN001
            calls.append((template, ctx))
            return "<should-not-happen>"

        from core.templating import manager
        original = manager.template_manager._renderer
        try:
            class _Trap:
                def render(self, template, context):
                    calls.append((template, context))
                    return ""
            manager.template_manager._renderer = _Trap()

            request = FakeRequest("GET", "/welcome")
            response = module.WelcomeController.index(request)
            assert response.body == b"Bonjour Forge"
            assert calls == [], (
                f"`index` ne doit appeler aucun template, mais a appelé : {calls}"
            )
        finally:
            manager.template_manager._renderer = original


# ── 5. Étape suivante : request.param ────────────────────────────────────────


class TestGreetStepUsesRequestParam:
    def test_greet_documente_request_param(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert 'request.param("name", default="Forge")' in content

    def test_greet_repond_avec_le_nom_par_defaut(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_welcome_controller_greet", _CONTROLLER,
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        response = module.WelcomeController.greet(FakeRequest("GET", "/welcome/greet"))
        assert response.body == b"Bonjour Forge"

    def test_greet_repond_avec_le_nom_fourni(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_welcome_controller_greet_named", _CONTROLLER,
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        request = FakeRequest("GET", "/welcome/greet", params={"name": "Roger"})
        response = module.WelcomeController.greet(request)
        assert response.body == b"Bonjour Roger"


# ── 6. Étape suivante : Response.debug(request.data) ─────────────────────────


class TestInspectStepUsesResponseDebug:
    def test_inspect_documente_response_debug(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "Response.debug(request.data)" in content

    def test_inspect_retourne_text_html_en_dev(self):
        """En `APP_ENV=dev`, `Response.debug` produit un dump HTML
        pédagogique (DX-DEBUG-DUMP-HTML-001)."""
        from core import forge as forge_module
        original_env = forge_module._cfg.get("app_env", "dev")
        forge_module._cfg["app_env"] = "dev"
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "_welcome_controller_inspect", _CONTROLLER,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            response = module.WelcomeController.inspect(FakeRequest("GET", "/welcome/inspect"))
            assert response.content_type == "text/html; charset=utf-8"
            # Le dump contient le path de la requête.
            assert b"/welcome/inspect" in response.body
            assert b"Debug Forge" in response.body
        finally:
            forge_module._cfg["app_env"] = original_env

    def test_inspect_refuse_en_prod(self):
        """En `APP_ENV=prod`, `Response.debug` refuse et retourne 404."""
        from core import forge as forge_module
        original_env = forge_module._cfg.get("app_env", "dev")
        forge_module._cfg["app_env"] = "prod"
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "_welcome_controller_inspect_prod", _CONTROLLER,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            response = module.WelcomeController.inspect(FakeRequest("GET", "/welcome/inspect"))
            assert response.status == 404
            # Aucune fuite du path /welcome/inspect dans le body
            assert b"/welcome/inspect" not in response.body
        finally:
            forge_module._cfg["app_env"] = original_env


# ── 7. render() vient APRÈS dans la progression ──────────────────────────────


class TestRenderComesAfterResponseText:
    """`BaseController.render(...)` reste documenté, mais arrive après
    `Response.text(...)` / `Response.debug(...)` dans la progression."""

    def test_render_documente(self):
        content = _DOC.read_text(encoding="utf-8")
        assert "BaseController.render" in content

    def test_response_text_apparait_avant_render_dans_doc(self):
        """L'ordre pédagogique est verrouillé : Response.text précède render."""
        content = _DOC.read_text(encoding="utf-8")
        idx_text = content.find('Response.text("Bonjour Forge")')
        idx_render = content.find("BaseController.render")
        assert idx_text != -1, "Response.text doit être présent dans la doc"
        assert idx_render != -1, "BaseController.render doit être présent dans la doc"
        assert idx_text < idx_render, (
            "La doc doit montrer Response.text AVANT BaseController.render "
            "(progression pédagogique)"
        )

    def test_response_debug_apparait_avant_render_dans_doc(self):
        content = _DOC.read_text(encoding="utf-8")
        idx_debug = content.find("Response.debug")
        idx_render = content.find("BaseController.render")
        assert idx_debug != -1 and idx_render != -1
        assert idx_debug < idx_render, (
            "Response.debug doit être introduit AVANT BaseController.render"
        )


# ── 8. Cohérence routes vs contrôleur ────────────────────────────────────────


class TestRoutesSnippetCoherent:
    def test_routes_snippet_appelle_les_8_methodes(self):
        snippet = (_STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        expected = [
            "WelcomeController.index",
            "WelcomeController.greet",
            "WelcomeController.inspect",
            "WelcomeController.cycle",
            "WelcomeController.request_example",
            "WelcomeController.response_example",
            "WelcomeController.routing_example",
            "WelcomeController.not_found_demo",
        ]
        for handler in expected:
            assert handler in snippet, (
                f"Le snippet de routes doit câbler {handler}"
            )


# ── 9. Compilabilité ─────────────────────────────────────────────────────────


class TestControllerCompiles:
    def test_le_controleur_parse(self):
        ast.parse(_CONTROLLER.read_text(encoding="utf-8"))


# ── 10. Anti-régression — la vue retirée n'est pas réintroduite ──────────────


class TestRetiredViewStaysGone:
    def test_welcome_index_html_n_existe_plus(self):
        path = _STARTER_DIR / "files" / "mvc" / "views" / "welcome" / "index.html"
        assert not path.exists(), (
            "STARTER-BONJOUR-FORGE-001 : `welcome/index.html` est retirée "
            "définitivement. La route /welcome retourne désormais "
            "Response.text(\"Bonjour Forge\")."
        )
