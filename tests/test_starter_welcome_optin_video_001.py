"""Tests — STARTER-WELCOME-VIDEO-001.

Vérifie le contrat pédagogique du starter d'entrée Forge Video :

  1. Le starter existe et est résolvable par identifiant + aliases.
  2. ``starter.json`` est valide : nom « Bonjour Vidéo », `requires_db: false`,
     number 17, aliases `welcome-optin-video`/`video`/`17`.
  3. Le contrôleur livré importe `Request`, `Response`,
     `forge_mvc_video.config` et `forge_mvc_video.storage.repository`, et
     expose trois méthodes typées `Request -> Response`.
  4. `index` retourne ``Response.text("Bonjour Forge Video")``.
  5. `inspect` retourne un JSON de configuration, token **toujours masqué**.
  6. `list` retourne une réponse pédagogique `video_storage_not_ready`
     (HTTP 503) quand le repository échoue, pas une trace technique.
  7. Le starter ne touche pas `core/`, ne lance aucun ffmpeg, n'écrit pas
     en base.
  8. La documentation existe et la nav la liste.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from forge_cli.starters.registry import resolve
from tests.fake_request import FakeRequest


_REPO_ROOT = Path(__file__).resolve().parent.parent
_STARTER_DIR = _REPO_ROOT / "forge_cli" / "starters" / "data" / "welcome-optin-video"
_STARTER_JSON = _STARTER_DIR / "starter.json"
_ROUTES_SNIPPET = _STARTER_DIR / "routes.py.snippet"
_CONTROLLER = (
    _STARTER_DIR / "files" / "mvc" / "controllers"
    / "welcome_optin_video_controller.py"
)
_DOC = _REPO_ROOT / "docs" / "starters" / "optin-video" / "welcome-optin-video.md"
_DOC_INDEX = _REPO_ROOT / "docs" / "starters" / "optin-video" / "index.md"
_STARTERS_INDEX = _REPO_ROOT / "docs" / "starters" / "index.md"
_MKDOCS_YML = _REPO_ROOT / "mkdocs.yml"
_CORE_DIR = _REPO_ROOT / "core"


# ── 1. Présence & métadonnées ───────────────────────────────────────────────


class TestStarterPresence:
    def test_starter_dir_exists(self):
        assert _STARTER_DIR.is_dir()

    def test_starter_json_exists(self):
        assert _STARTER_JSON.exists()

    def test_routes_snippet_exists(self):
        assert _ROUTES_SNIPPET.exists()

    def test_controller_exists(self):
        assert _CONTROLLER.exists()


class TestStarterJsonContract:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.meta = json.loads(_STARTER_JSON.read_text(encoding="utf-8"))

    def test_id(self):
        assert self.meta["id"] == "welcome-optin-video"

    def test_public_name(self):
        assert self.meta["name"] == "Bonjour Vidéo"

    def test_kind_skeleton(self):
        assert self.meta["kind"] == "skeleton"

    def test_requires_db_false(self):
        assert self.meta["requires_db"] is False

    def test_number_seventeen(self):
        assert self.meta["number"] == 17

    def test_home_route(self):
        assert self.meta["home_route"] == "/welcome-optin-video"

    def test_routes_marker(self):
        assert self.meta["routes_marker"] == "welcome-optin-video"

    def test_routes_snippet_relative_path(self):
        assert self.meta["routes_snippet"] == "routes.py.snippet"

    @pytest.mark.parametrize(
        "alias",
        ["welcome-optin-video", "welcome_optin_video", "bonjour-video",
         "bonjour_video", "video", "17"],
    )
    def test_alias_resolvable(self, alias):
        resolved = resolve(alias)
        assert resolved["id"] == "welcome-optin-video"

    def test_available_status(self):
        assert self.meta["status"] == "available"

    def test_check_paths_lists_controller(self):
        assert (
            "mvc/controllers/welcome_optin_video_controller.py"
            in self.meta["check_paths"]
        )


# ── 2. Routes snippet ──────────────────────────────────────────────────────


class TestRoutesSnippet:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = _ROUTES_SNIPPET.read_text(encoding="utf-8")

    def test_has_start_end_markers(self):
        assert "# forge-starter:welcome-optin-video:start" in self.text
        assert "# forge-starter:welcome-optin-video:end" in self.text

    @pytest.mark.parametrize(
        "url",
        [
            "/welcome-optin-video",
            "/welcome-optin-video/inspect",
            "/welcome-optin-video/list",
        ],
    )
    def test_route_url_present(self, url):
        assert f'"{url}"' in self.text

    def test_imports_controller(self):
        assert (
            "from mvc.controllers.welcome_optin_video_controller "
            "import WelcomeVideoController"
        ) in self.text

    def test_branches_optins_not_video_routes_directly(self):
        assert "from optins.registry import register_optins" in self.text
        assert "register_optins(router)" in self.text
        assert "from forge_mvc_video import register_video_routes" not in self.text

    def test_routes_in_public_group(self):
        assert 'router.group("", public=True)' in self.text


# ── 3. Contrôleur — structure statique (AST) ───────────────────────────────


class TestControllerStaticContract:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = _CONTROLLER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.text)

    def test_imports_request_response(self):
        assert "from core.http.request import Request" in self.text
        assert "from core.http.response import Response" in self.text

    def test_imports_base_controller(self):
        assert (
            "from core.mvc.controller.base_controller import BaseController"
            in self.text
        )

    def test_imports_forge_mvc_video_explicitly(self):
        assert "from forge_mvc_video.config import load_video_config" in self.text
        assert (
            "from forge_mvc_video.storage.repository import VideoRepository"
            in self.text
        )

    def test_class_exists_and_extends_base_controller(self):
        classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)]
        controller = next(
            (c for c in classes if c.name == "WelcomeVideoController"), None,
        )
        assert controller is not None
        bases = [ast.unparse(b) for b in controller.bases]
        assert "BaseController" in bases

    @pytest.mark.parametrize("method", ["index", "inspect", "list"])
    def test_method_typed_request_response(self, method):
        assert f"def {method}(request: Request) -> Response" in self.text


# ── 4. Comportement runtime — avec FakeRequest ─────────────────────────────


@pytest.fixture
def controller_module():
    import importlib
    import sys

    controllers_dir = _CONTROLLER.parent
    sys.path.insert(0, str(controllers_dir))
    try:
        sys.modules.pop("welcome_optin_video_controller", None)
        module = importlib.import_module("welcome_optin_video_controller")
        yield module
    finally:
        sys.path.remove(str(controllers_dir))
        sys.modules.pop("welcome_optin_video_controller", None)


class TestControllerIndex:
    def test_returns_bonjour_forge_video(self, controller_module):
        ctrl = controller_module.WelcomeVideoController
        resp = ctrl.index(FakeRequest("GET", "/welcome-optin-video"))
        assert resp.status == 200
        assert resp.content_type.startswith("text/plain")
        assert resp.body == b"Bonjour Forge Video"


class TestControllerInspect:
    def test_returns_json_with_default_config(self, controller_module):
        ctrl = controller_module.WelcomeVideoController
        resp = ctrl.inspect(FakeRequest("GET", "/welcome-optin-video/inspect"))
        assert resp.status == 200
        assert resp.content_type.startswith("application/json")
        data = json.loads(resp.body.decode("utf-8"))
        assert data["ffmpeg_bin"] == "ffmpeg"
        assert data["ffprobe_bin"] == "ffprobe"
        assert data["api_token"] is None

    def test_masks_token_when_set(self, controller_module, monkeypatch):
        monkeypatch.setenv("FORGE_VIDEO_API_TOKEN", "s3cr3t-token")
        ctrl = controller_module.WelcomeVideoController
        resp = ctrl.inspect(FakeRequest("GET", "/welcome-optin-video/inspect"))
        body = resp.body.decode("utf-8")
        assert "s3cr3t-token" not in body, (
            "Le token ne doit jamais apparaître en clair"
        )
        data = json.loads(body)
        assert data["api_token"] == "***"


class TestControllerListFallback:
    def test_list_returns_pedagogical_503_on_error(self, controller_module):
        with patch.object(controller_module, "VideoRepository") as fake_repo_class:
            fake_repo_class.return_value.list_recent.side_effect = RuntimeError(
                "Table 'videos' doesn't exist"
            )
            ctrl = controller_module.WelcomeVideoController
            resp = ctrl.list(FakeRequest("GET", "/welcome-optin-video/list"))
            assert resp.status == 503
            data = json.loads(resp.body.decode("utf-8"))
            assert data["error"] == "video_storage_not_ready"
            assert "migration" in data["message"].lower()

    def test_list_returns_videos_envelope_on_success(self, controller_module):
        with patch.object(controller_module, "VideoRepository") as fake_repo_class:
            fake_repo_class.return_value.list_recent.return_value = [
                {"id": 1, "uuid": "u-1", "status": "ready"},
            ]
            ctrl = controller_module.WelcomeVideoController
            resp = ctrl.list(FakeRequest("GET", "/welcome-optin-video/list"))
            assert resp.status == 200
            data = json.loads(resp.body.decode("utf-8"))
            assert data == {"videos": [{"id": 1, "uuid": "u-1", "status": "ready"}]}


# ── 5. Garde-fous périmètre ────────────────────────────────────────────────


class TestNoHeavyProcessing:
    """Le starter ne lance aucun ffmpeg — c'est de la lecture HTTP."""

    def test_controller_does_not_transcode(self):
        text = _CONTROLLER.read_text(encoding="utf-8")
        # La docstring peut mentionner « sans ffmpeg » à titre pédagogique ;
        # le garde porte sur l'absence d'invocation réelle de traitement.
        assert "process_video" not in text
        assert "subprocess" not in text
        assert "transcode" not in text


class TestNoWriteToDb:
    def test_controller_does_not_call_insert(self):
        text = _CONTROLLER.read_text(encoding="utf-8")
        assert ".insert(" not in text


class TestNoCoreImportsVideo:
    def test_no_core_module_imports_forge_mvc_video(self):
        offenders: list[Path] = []
        for py in _CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_video" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders


# ── 6. Documentation ────────────────────────────────────────────────────────


class TestDocumentation:
    def test_doc_exists(self):
        assert _DOC.exists()

    def test_doc_h1_is_bonjour_video(self):
        first_line = _DOC.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "# Bonjour Vidéo"

    def test_doc_index_overview_exists(self):
        assert _DOC_INDEX.exists()

    def test_starters_index_lists_welcome_optin_video(self):
        text = _STARTERS_INDEX.read_text(encoding="utf-8")
        assert "welcome-optin-video" in text
        assert "Bonjour Vidéo" in text

    def test_mkdocs_nav_lists_welcome_optin_video(self):
        text = _MKDOCS_YML.read_text(encoding="utf-8")
        assert "starters/optin-video/welcome-optin-video.md" in text
