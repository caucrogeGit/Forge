"""Tests — STARTER-WELCOME-IOT-001.

Vérifie le contrat pédagogique du starter d'entrée Forge IoT :

  1. Le starter existe et est résolvable par identifiant + aliases.
  2. ``starter.json`` est valide et déclare le nom public
     « Bonjour IoT », `requires_db: false`, alias `welcome-iot`/`iot`.
  3. Le contrôleur livré importe `Request`, `Response`,
     `forge_mvc_iot.config` et `forge_mvc_iot.storage`, et expose
     quatre méthodes typées `Request -> Response`.
  4. `index` retourne ``Response.text("Bonjour Forge IoT")``.
  5. `inspect` retourne un JSON avec la configuration, mot de passe
     **toujours masqué** par `***` (ou `null` si absent).
  6. `events` et `find_by_device` retournent une réponse pédagogique
     `iot_storage_not_ready` (HTTP 503) quand le repository échoue,
     pas une trace technique.
  7. Le starter ne touche pas `core/`, ne lance pas de subscriber,
     n'écrit pas en base, ne dépend pas d'un broker MQTT actif.
  8. La documentation existe et la roadmap mentionne le ticket.
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
_STARTER_DIR = _REPO_ROOT / "forge_cli" / "starters" / "data" / "welcome-iot"
_STARTER_JSON = _STARTER_DIR / "starter.json"
_ROUTES_SNIPPET = _STARTER_DIR / "routes.py.snippet"
_CONTROLLER = (
    _STARTER_DIR / "files" / "mvc" / "controllers"
    / "welcome_iot_controller.py"
)
_DOC = _REPO_ROOT / "docs" / "starters" / "welcome-iot" / "index.md"
_STARTERS_INDEX = _REPO_ROOT / "docs" / "starters" / "index.md"
_MKDOCS_YML = _REPO_ROOT / "mkdocs.yml"
_ROADMAP = _REPO_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
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
        assert self.meta["id"] == "welcome-iot"

    def test_public_name(self):
        assert self.meta["name"] == "Bonjour IoT"

    def test_kind_skeleton(self):
        assert self.meta["kind"] == "skeleton"

    def test_requires_db_false(self):
        # Le starter doit fonctionner sans `forge db:init`.
        assert self.meta["requires_db"] is False

    def test_home_route(self):
        assert self.meta["home_route"] == "/welcome-iot"

    def test_routes_marker(self):
        assert self.meta["routes_marker"] == "welcome-iot"

    def test_routes_snippet_relative_path(self):
        assert self.meta["routes_snippet"] == "routes.py.snippet"

    @pytest.mark.parametrize(
        "alias",
        ["welcome-iot", "welcome_iot", "bonjour-iot", "bonjour_iot", "iot", "15"],
    )
    def test_alias_resolvable(self, alias):
        resolved = resolve(alias)
        assert resolved["id"] == "welcome-iot"

    def test_available_status(self):
        assert self.meta["status"] == "available"

    def test_check_paths_lists_controller(self):
        assert (
            "mvc/controllers/welcome_iot_controller.py"
            in self.meta["check_paths"]
        )


# ── 2. Routes snippet ──────────────────────────────────────────────────────


class TestRoutesSnippet:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = _ROUTES_SNIPPET.read_text(encoding="utf-8")

    def test_has_start_end_markers(self):
        assert "# forge-starter:welcome-iot:start" in self.text
        assert "# forge-starter:welcome-iot:end" in self.text

    @pytest.mark.parametrize(
        "url",
        [
            "/welcome-iot",
            "/welcome-iot/inspect",
            "/welcome-iot/events",
            "/welcome-iot/device/{site}/{device_id}",
        ],
    )
    def test_route_url_present(self, url):
        assert f'"{url}"' in self.text, (
            f"La route {url} doit être déclarée dans le snippet"
        )

    def test_imports_controller(self):
        assert (
            "from mvc.controllers.welcome_iot_controller "
            "import WelcomeIotController"
        ) in self.text

    def test_imports_register_iot_routes(self):
        # Le starter expose aussi l'API officielle.
        assert "from forge_mvc_iot import register_iot_routes" in self.text
        assert "register_iot_routes(router)" in self.text

    def test_routes_in_public_group(self):
        # Toutes les routes sont publiques — pas d'auth dans ce starter.
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

    def test_imports_forge_mvc_iot_explicitly(self):
        # Le starter doit importer le module opt-in explicitement —
        # c'est tout l'intérêt pédagogique.
        assert "from forge_mvc_iot.config import load_iot_config" in self.text
        assert "from forge_mvc_iot.storage import IotEventRepository" in self.text

    def test_class_exists_and_extends_base_controller(self):
        classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)]
        controller = next(
            (c for c in classes if c.name == "WelcomeIotController"), None,
        )
        assert controller is not None
        bases = [ast.unparse(b) for b in controller.bases]
        assert "BaseController" in bases

    @pytest.mark.parametrize(
        "method", ["index", "inspect", "events", "find_by_device"],
    )
    def test_method_typed_request_response(self, method):
        # Chaque méthode doit avoir la signature
        # `request: Request) -> Response`.
        assert f"def {method}(request: Request) -> Response" in self.text, (
            f"La méthode {method} doit être typée Request -> Response"
        )


# ── 4. Comportement runtime — avec FakeRequest ─────────────────────────────


@pytest.fixture
def controller_module():
    """Importe le contrôleur via sys.path après injection du dossier
    `files/mvc/controllers/`.

    Le starter est livré tel quel ; on doit pouvoir importer son
    contrôleur depuis les tests sans recopier le starter dans un
    projet de test.
    """
    import importlib
    import sys

    controllers_dir = _CONTROLLER.parent
    sys.path.insert(0, str(controllers_dir))
    try:
        if "welcome_iot_controller" in sys.modules:
            del sys.modules["welcome_iot_controller"]
        module = importlib.import_module("welcome_iot_controller")
        yield module
    finally:
        sys.path.remove(str(controllers_dir))
        sys.modules.pop("welcome_iot_controller", None)


class TestControllerIndex:
    def test_returns_bonjour_forge_iot(self, controller_module):
        ctrl = controller_module.WelcomeIotController
        resp = ctrl.index(FakeRequest("GET", "/welcome-iot"))
        assert resp.status == 200
        assert resp.content_type.startswith("text/plain")
        assert resp.body == b"Bonjour Forge IoT"


class TestControllerInspect:
    def test_returns_json_with_default_config(self, controller_module):
        ctrl = controller_module.WelcomeIotController
        resp = ctrl.inspect(FakeRequest("GET", "/welcome-iot/inspect"))
        assert resp.status == 200
        assert resp.content_type.startswith("application/json")
        data = json.loads(resp.body.decode("utf-8"))
        # Défauts FORGE_IOT_* sans variables d'environnement positionnées.
        assert data["mqtt_host"] == "localhost"
        assert data["mqtt_port"] == 1883
        assert data["mqtt_topic"] == "forge/+/+/telemetry"
        assert data["mqtt_client_id"] == "forge-iot"
        assert data["mqtt_username"] is None
        assert data["mqtt_password"] is None

    def test_masks_password_when_set(self, controller_module, monkeypatch):
        monkeypatch.setenv("FORGE_IOT_MQTT_USERNAME", "forge")
        monkeypatch.setenv("FORGE_IOT_MQTT_PASSWORD", "s3cr3t")
        ctrl = controller_module.WelcomeIotController
        resp = ctrl.inspect(FakeRequest("GET", "/welcome-iot/inspect"))
        body = resp.body.decode("utf-8")
        assert "s3cr3t" not in body, (
            "Le mot de passe ne doit jamais apparaître en clair"
        )
        data = json.loads(body)
        assert data["mqtt_username"] == "forge"
        assert data["mqtt_password"] == "***"


class TestControllerEventsFallback:
    """Quand le repository échoue (table absente, base coupée…), la
    réponse doit rester pédagogique — pas de stacktrace côté client."""

    def test_events_returns_pedagogical_503_on_error(self, controller_module):
        with patch.object(
            controller_module, "IotEventRepository",
        ) as fake_repo_class:
            fake_repo_class.return_value.list_recent.side_effect = RuntimeError(
                "Table 'iot_events' doesn't exist"
            )
            ctrl = controller_module.WelcomeIotController
            resp = ctrl.events(FakeRequest("GET", "/welcome-iot/events"))
            assert resp.status == 503
            data = json.loads(resp.body.decode("utf-8"))
            assert data["error"] == "iot_storage_not_ready"
            assert "migration" in data["message"].lower()
            # Aucune fuite de la trace ni du nom de la table technique.
            body_text = resp.body.decode("utf-8")
            assert "Table" not in body_text or "Applique" in body_text

    def test_events_returns_events_envelope_on_success(self, controller_module):
        with patch.object(
            controller_module, "IotEventRepository",
        ) as fake_repo_class:
            fake_repo_class.return_value.list_recent.return_value = [
                {"id": 1, "kind": "temperature", "value": 22.4},
            ]
            ctrl = controller_module.WelcomeIotController
            resp = ctrl.events(FakeRequest("GET", "/welcome-iot/events"))
            assert resp.status == 200
            data = json.loads(resp.body.decode("utf-8"))
            assert data == {"events": [{"id": 1, "kind": "temperature", "value": 22.4}]}


class TestControllerFindByDevice:
    def test_returns_pedagogical_503_on_error(self, controller_module):
        with patch.object(
            controller_module, "IotEventRepository",
        ) as fake_repo_class:
            fake_repo_class.return_value.find_by_device.side_effect = RuntimeError(
                "boom"
            )
            ctrl = controller_module.WelcomeIotController
            req = FakeRequest("GET", "/welcome-iot/device/atelier/esp32-001")
            req.route_params = {"site": "atelier", "device_id": "esp32-001"}
            resp = ctrl.find_by_device(req)
            assert resp.status == 503
            data = json.loads(resp.body.decode("utf-8"))
            assert data["error"] == "iot_storage_not_ready"

    def test_returns_events_envelope_with_site_and_device_id(
        self, controller_module,
    ):
        with patch.object(
            controller_module, "IotEventRepository",
        ) as fake_repo_class:
            fake_repo_class.return_value.find_by_device.return_value = [
                {"id": 7, "kind": "humidity", "value": 47},
            ]
            ctrl = controller_module.WelcomeIotController
            req = FakeRequest("GET", "/welcome-iot/device/atelier/esp32-001")
            req.route_params = {"site": "atelier", "device_id": "esp32-001"}
            resp = ctrl.find_by_device(req)
            assert resp.status == 200
            data = json.loads(resp.body.decode("utf-8"))
            assert data["site"] == "atelier"
            assert data["device_id"] == "esp32-001"
            assert data["events"] == [{"id": 7, "kind": "humidity", "value": 47}]
            # Le repository a bien reçu site et device_id (vient du topic
            # de route).
            fake_repo_class.return_value.find_by_device.assert_called_once_with(
                "atelier", "esp32-001", limit=20,
            )


# ── 5. Garde-fous périmètre ────────────────────────────────────────────────


class TestNoAutomaticSubscriber:
    """Le starter ne lance jamais le subscriber MQTT — c'est de la
    lecture HTTP uniquement."""

    def test_controller_does_not_import_subscriber(self):
        text = _CONTROLLER.read_text(encoding="utf-8")
        assert "mqtt.subscriber" not in text
        assert "MqttSubscriber" not in text

    def test_snippet_does_not_start_subscriber(self):
        text = _ROUTES_SNIPPET.read_text(encoding="utf-8")
        assert "MqttSubscriber" not in text
        assert "loop_forever" not in text
        assert "loop_start" not in text


class TestNoWriteToDb:
    """Le starter ne fait que de la LECTURE."""

    def test_controller_does_not_call_insert(self):
        text = _CONTROLLER.read_text(encoding="utf-8")
        assert ".insert(" not in text


class TestNoCoreImportsIot:
    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in _CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders


# ── 6. Documentation ────────────────────────────────────────────────────────


class TestDocumentation:
    def test_doc_index_exists(self):
        assert _DOC.exists()

    def test_doc_h1_is_bonjour_iot(self):
        first_line = _DOC.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "# Bonjour IoT"

    def test_starters_index_lists_welcome_iot(self):
        text = _STARTERS_INDEX.read_text(encoding="utf-8")
        assert "welcome-iot" in text
        assert "Bonjour IoT" in text

    def test_mkdocs_nav_lists_welcome_iot(self):
        text = _MKDOCS_YML.read_text(encoding="utf-8")
        assert "starters/welcome-iot/index.md" in text

    def test_roadmap_mentions_ticket(self):
        text = _ROADMAP.read_text(encoding="utf-8")
        assert "STARTER-WELCOME-IOT-001" in text
