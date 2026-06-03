"""Tests — STARTER-BONJOUR-FORGE-MINIMAL-001.

Vérifie le contrat pédagogique du starter d'entrée ramené à un premier
contact minimal :

  1. Le starter est nommé « Bonjour Forge » (libellé public conservé).
  2. Le contrôleur livré importe `Request` et `Response`.
  3. La méthode `index` est annotée `request: Request -> Response`.
  4. `index` retourne `Response.text("Bonjour Forge")` — aucun template.
  5. Palier 1 = une seule responsabilité (réponse texte) : la lecture
     d'un paramètre d'URL (`request.param`) appartient au palier suivant
     (`query-params`), pas ici.
  6. Le contrôleur n'expose AUCUNE autre méthode publique (pas de
     `greet`, `inspect`, `cycle`, `request_example`, `response_example`,
     `routing_example`, `not_found_demo`).
  7. Les vues HTML précédemment livrées sont retirées définitivement.
  8. Les anciens alias (`welcome`, `bienvenue`, `7`) restent
     résolvables ; les nouveaux (`bonjour`, `bonjour-forge`) aussi.

Les tests évitent toute exécution réelle du serveur HTTP : ils exécutent
les méthodes du contrôleur avec une `FakeRequest` en mémoire.
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
_VIEWS_DIR = _STARTER_DIR / "files" / "mvc" / "views" / "welcome"
_STARTER_JSON = _STARTER_DIR / "starter.json"
_DOC = _REPO_ROOT / "docs" / "starters" / "welcome-forge" / "debutant" / "welcome.md"
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
    "cycle.html",
    "request_example.html",
    "response_example.html",
    "routing_example.html",
    "not_found_demo.html",
)


# ── 1. Libellé public conservé ───────────────────────────────────────────────


class TestStarterNameKeptAsBonjourForge:
    def test_starter_json_name_est_bonjour_forge(self):
        meta = json.loads(_STARTER_JSON.read_text(encoding="utf-8"))
        assert meta["name"] == "Bonjour Forge"

    def test_doc_h1_est_bonjour_forge(self):
        content = _DOC.read_text(encoding="utf-8")
        assert content.splitlines()[0] == "# Bonjour Forge"


# ── 2. Aliases conservés ─────────────────────────────────────────────────────


class TestStarterAliases:
    @pytest.mark.parametrize("alias", ["welcome", "bienvenue", "4"])
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
    """L'action publique `index` est typée `request: Request -> Response`."""

    @pytest.mark.parametrize("method", ["index"])
    def test_signature_typee(self, method):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert f"def {method}(request: Request) -> Response:" in content


# ── 4. `index` retourne Response.text("Bonjour Forge") sans template ─────────


class TestIndexReturnsResponseText:
    def _load_controller_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_welcome_controller_minimal", _CONTROLLER,
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_index_appelle_response_text_bonjour_forge(self):
        module = self._load_controller_module()
        response = module.WelcomeController.index(FakeRequest("GET", "/welcome"))
        assert response.status == 200
        assert response.content_type == "text/plain; charset=utf-8"
        assert response.body == b"Bonjour Forge"

    def test_index_n_ouvre_aucun_template(self):
        module = self._load_controller_module()
        calls: list[tuple[str, dict]] = []

        from core.templating import manager
        original = manager.template_manager._renderer
        try:
            class _Trap:
                def render(self, template, context):
                    calls.append((template, context))
                    return ""
            manager.template_manager._renderer = _Trap()

            response = module.WelcomeController.index(FakeRequest("GET", "/welcome"))
            assert response.body == b"Bonjour Forge"
            assert calls == [], (
                f"`index` ne doit appeler aucun template, mais a appelé : {calls}"
            )
        finally:
            manager.template_manager._renderer = original


# ── 5. `request.param` (palier 2) absent du palier 1 ─────────────────────────


class TestNoUrlParamInWelcome:
    """Palier 1 = une seule responsabilité (réponse texte). La lecture
    d'un paramètre d'URL appartient au palier 2 (`query-params`)."""

    def test_controleur_ne_lit_aucun_parametre_url(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "request.param" not in content, (
            "Le starter welcome (palier 1) ne doit pas utiliser request.param "
            "— c'est la responsabilité du palier query-params."
        )

    def test_pas_de_methode_greet(self):
        content = _CONTROLLER.read_text(encoding="utf-8")
        assert "def greet" not in content


# ── 6. Le contrôleur n'expose que index ──────────────────────────────────────


class TestControllerHasOnlyIndex:
    def _public_methods(self) -> set[str]:
        tree = ast.parse(_CONTROLLER.read_text(encoding="utf-8"))
        names: set[str] = set()
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef):
                continue
            if cls.name != "WelcomeController":
                continue
            for node in cls.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    names.add(node.name)
        return names

    def test_exactement_index(self):
        assert self._public_methods() == {"index"}, (
            "Le contrat minimal n'expose que `index` (palier 1 = une seule "
            "responsabilité : réponse texte)."
        )

    @pytest.mark.parametrize("method", _RETIRED_METHODS)
    def test_methode_retiree_absente(self, method):
        assert method not in self._public_methods(), (
            f"La méthode `{method}` doit être retirée du starter minimal "
            "(STARTER-BONJOUR-FORGE-MINIMAL-001)."
        )


# ── 7. Les vues HTML sont retirées définitivement ────────────────────────────


class TestRetiredViewsStayGone:
    def test_dossier_views_welcome_absent(self):
        assert not _VIEWS_DIR.exists(), (
            "Le dossier `mvc/views/welcome/` doit être retiré du starter minimal."
        )

    @pytest.mark.parametrize("view", _RETIRED_VIEWS + ("index.html",))
    def test_vue_retiree_absente(self, view: str):
        assert not (_VIEWS_DIR / view).exists(), (
            f"La vue `{view}` doit être retirée du starter minimal."
        )


# ── 8. Cohérence routes ↔ contrôleur ─────────────────────────────────────────


class TestRoutesSnippetCoherent:
    def test_snippet_appelle_exactement_index(self):
        snippet = (_STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
        assert "WelcomeController.index" in snippet
        for method in _RETIRED_METHODS:
            assert f"WelcomeController.{method}" not in snippet, (
                f"Le snippet ne doit plus référencer `WelcomeController.{method}`."
            )


# ── 9. Compilabilité ─────────────────────────────────────────────────────────


class TestControllerCompiles:
    def test_le_controleur_parse(self):
        ast.parse(_CONTROLLER.read_text(encoding="utf-8"))
