"""Tests de l'API HTTP JSON Forge IoT — IOT-HTTP-API-001.

Vérifie le branchement entre les trois routes GET de
``forge_mvc_iot.http`` et ``IotEventRepository``.

Aucun MariaDB, aucun broker : un ``MagicMock`` est injecté comme
``repository`` et on observe les appels. Les handlers sont obtenus via
``router.resolve(...)`` puis appelés directement avec un
``FakeRequest`` (le routeur peuple ``request.route_params``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.http.router import Router
pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.http import (
    ERROR_INTERNAL,
    ERROR_INVALID_LIMIT,
    ROUTE_DEVICE_COUNT,
    ROUTE_EVENTS_BY_DEVICE,
    ROUTE_LIST_EVENTS,
    IotHttpController,
    register_iot_routes,
)
from forge_mvc_iot.storage.repository import DEFAULT_LIMIT, MAX_LIMIT
from forge_mvc_testing import FakeRequest

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
HTTP_MODULE_FILE = IOT_PKG_DIR / "forge_mvc_iot" / "http.py"
CORE_DIR = PROJECT_ROOT / "core"


# ── Helpers de fixture ──────────────────────────────────────────────────────


def _event_row(
    *,
    id: int = 1,
    site: str = "atelier",
    device_id: str = "esp32-001",
    kind: str = "temperature",
    value: float = 22.4,
    unit: str = "°C",
    timestamp: str = "2026-05-28T10:00:00Z",
    metadata: dict | None = None,
    received_at: datetime | None = None,
) -> dict:
    """Construit une ligne telle que retournée par le repository
    (``metadata`` déjà parsée, ``received_at`` en ``datetime``)."""
    return {
        "id": id,
        "site": site,
        "device_id": device_id,
        "kind": kind,
        "value": value,
        "unit": unit,
        "timestamp": timestamp,
        "metadata": metadata,
        "received_at": received_at or datetime(
            2026, 5, 28, 10, 0, 5, tzinfo=UTC,
        ),
    }


def _resolve_handler(router: Router, method: str, path: str):
    """Retourne (handler, route_params) ou échoue le test."""
    result = router.resolve(method, path)
    assert result is not None, f"Aucune route ne matche {method} {path!r}"
    return result


def _body_json(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


# ═══════════════════════════════════════════════════════════════════════════
# Enregistrement des routes
# ═══════════════════════════════════════════════════════════════════════════


class TestRegisterIotRoutes:
    def test_register_adds_the_read_routes(self):
        """Les routes de lecture sont posées, chacune une fois.

        Le test exigeait auparavant `len(...) == 3`, ce qui figeait un compte
        et non la fin qu'il annonce. `IOT-AGGREGATES-001` en a ajouté deux, et
        un compte figé aurait forcé à le retoucher à chaque route sans rien
        vérifier de plus.
        """
        from forge_mvc_iot.http import (
            ROUTE_DEVICE_AGGREGATE,
            ROUTE_DEVICE_COUNT,
            ROUTE_EVENTS_BY_DEVICE,
            ROUTE_LIST_EVENTS,
            ROUTE_SITE_AGGREGATE,
        )

        router = Router()
        register_iot_routes(router, repository=MagicMock())

        motifs = [e.pattern for e in router._entries]
        attendues = [
            ROUTE_LIST_EVENTS, ROUTE_EVENTS_BY_DEVICE, ROUTE_DEVICE_COUNT,
            ROUTE_SITE_AGGREGATE, ROUTE_DEVICE_AGGREGATE,
        ]
        for attendue in attendues:
            assert motifs.count(attendue) == 1, f"route absente ou en double : {attendue}"
        assert len(motifs) == len(attendues)

    @pytest.mark.parametrize(
        "method, path",
        [
            ("GET", "/api/iot/events"),
            ("GET", "/api/iot/events/atelier/esp32-001"),
            ("GET", "/api/iot/devices/atelier/esp32-001/count"),
        ],
    )
    def test_routes_resolve(self, method, path):
        router = Router()
        register_iot_routes(router, repository=MagicMock())
        assert router.resolve(method, path) is not None

    def test_routes_have_stable_names(self):
        router = Router()
        register_iot_routes(router, repository=MagicMock())
        assert "iot_events_list" in router._named
        assert "iot_events_by_device" in router._named
        assert "iot_devices_count" in router._named

    def test_routes_are_public(self):
        router = Router()
        register_iot_routes(router, repository=MagicMock())
        for entry in router._entries:
            assert entry.public is True, (
                f"{entry.pattern} doit être public à ce ticket "
                "(pas d'authentification encore)"
            )

    def test_routes_marked_as_api(self):
        router = Router()
        register_iot_routes(router, repository=MagicMock())
        for entry in router._entries:
            assert entry.api is True

    def test_route_constants_match_patterns(self):
        router = Router()
        register_iot_routes(router, repository=MagicMock())
        patterns = {e.pattern for e in router._entries}
        assert ROUTE_LIST_EVENTS in patterns
        assert ROUTE_EVENTS_BY_DEVICE in patterns
        assert ROUTE_DEVICE_COUNT in patterns

    def test_register_uses_default_repository_when_none(self):
        # On vérifie juste que register_iot_routes(router) (sans
        # repository) ne lève pas — la construction de
        # IotEventRepository() est sûre (lazy import de core.database).
        router = Router()
        register_iot_routes(router)
        assert router._entries, "aucune route posée"


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/iot/events
# ═══════════════════════════════════════════════════════════════════════════


class TestListEventsRoute:
    def _setup(self, repo):
        router = Router()
        register_iot_routes(router, repository=repo)
        handler, _ = _resolve_handler(router, "GET", "/api/iot/events")
        return handler

    def test_default_limit_calls_repo_list_recent_with_100(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        handler = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/events")
        handler(req)
        repo.list_recent.assert_called_once_with(limit=DEFAULT_LIMIT)

    def test_custom_limit_query_param_is_forwarded(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        handler = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/events", params={"limit": "25"})
        handler(req)
        repo.list_recent.assert_called_once_with(limit=25)

    def test_returns_events_in_envelope(self):
        repo = MagicMock()
        repo.list_recent.return_value = [
            _event_row(id=1),
            _event_row(id=2, value=23.0),
        ]
        handler = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/events")
        resp = handler(req)
        assert resp.status == 200
        assert resp.content_type.startswith("application/json")
        body = _body_json(resp)
        assert "events" in body
        assert isinstance(body["events"], list)
        assert len(body["events"]) == 2
        assert body["events"][0]["id"] == 1
        assert body["events"][1]["value"] == 23.0

    def test_received_at_serialized_to_iso_z(self):
        repo = MagicMock()
        repo.list_recent.return_value = [
            _event_row(
                received_at=datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC),
            ),
        ]
        handler = self._setup(repo)
        body = _body_json(handler(FakeRequest("GET", "/api/iot/events")))
        assert body["events"][0]["received_at"] == "2026-05-28T10:00:05Z"

    def test_received_at_non_utc_converted_to_utc_z(self):
        # Fuseau Europe/Paris à 12:00:05 = UTC 10:00:05.
        paris = timezone(__import__("datetime").timedelta(hours=2))
        dt = datetime(2026, 5, 28, 12, 0, 5, tzinfo=paris)
        repo = MagicMock()
        repo.list_recent.return_value = [_event_row(received_at=dt)]
        handler = self._setup(repo)
        body = _body_json(handler(FakeRequest("GET", "/api/iot/events")))
        assert body["events"][0]["received_at"] == "2026-05-28T10:00:05Z"

    def test_metadata_json_key_never_present(self):
        repo = MagicMock()
        # On simule un consommateur indiscipliné qui aurait laissé fuiter
        # metadata_json — le contrôleur ne doit pas le propager.
        row = _event_row(metadata={"room": "atelier"})
        row["metadata_json"] = '{"leaked": true}'
        repo.list_recent.return_value = [row]
        handler = self._setup(repo)
        body = _body_json(handler(FakeRequest("GET", "/api/iot/events")))
        assert "metadata_json" not in body["events"][0]
        assert body["events"][0]["metadata"] == {"room": "atelier"}

    def test_metadata_none_serialized_as_null(self):
        repo = MagicMock()
        repo.list_recent.return_value = [_event_row(metadata=None)]
        handler = self._setup(repo)
        body = _body_json(handler(FakeRequest("GET", "/api/iot/events")))
        assert body["events"][0]["metadata"] is None

    def test_empty_list(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        handler = self._setup(repo)
        resp = handler(FakeRequest("GET", "/api/iot/events"))
        assert resp.status == 200
        assert _body_json(resp) == {"events": []}


class TestListEventsInvalidLimit:
    def _setup(self, repo):
        router = Router()
        register_iot_routes(router, repository=repo)
        handler, _ = _resolve_handler(router, "GET", "/api/iot/events")
        return handler

    @pytest.mark.parametrize("bad", ["abc", "0", "-1", "1001", "1.5", "1e3"])
    def test_invalid_limit_returns_400(self, bad):
        repo = MagicMock()
        handler = self._setup(repo)
        req = FakeRequest("GET", "/api/iot/events", params={"limit": bad})
        resp = handler(req)
        assert resp.status == 400
        body = _body_json(resp)
        assert body["error"] == ERROR_INVALID_LIMIT
        assert "message" in body
        # Le repository ne doit jamais avoir été appelé en cas de
        # limit invalide — la validation est côté contrôleur.
        repo.list_recent.assert_not_called()

    def test_empty_limit_uses_default(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        handler = self._setup(repo)
        req = FakeRequest("GET", "/api/iot/events", params={"limit": ""})
        handler(req)
        repo.list_recent.assert_called_once_with(limit=DEFAULT_LIMIT)

    def test_max_limit_accepted(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        handler = self._setup(repo)
        req = FakeRequest(
            "GET", "/api/iot/events", params={"limit": str(MAX_LIMIT)},
        )
        resp = handler(req)
        assert resp.status == 200
        repo.list_recent.assert_called_once_with(limit=MAX_LIMIT)


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/iot/events/{site}/{device_id}
# ═══════════════════════════════════════════════════════════════════════════


class TestEventsByDeviceRoute:
    def _setup(self, repo, *, params=None):
        router = Router()
        register_iot_routes(router, repository=repo)
        path = "/api/iot/events/atelier/esp32-001"
        result = router.resolve("GET", path)
        assert result is not None
        handler, route_params = result
        return handler, route_params

    def test_route_extracts_site_and_device_id(self):
        repo = MagicMock()
        repo.find_by_device.return_value = []
        handler, route_params = self._setup(repo)
        assert route_params == {"site": "atelier", "device_id": "esp32-001"}

    def test_calls_repo_find_by_device_with_route_params(self):
        repo = MagicMock()
        repo.find_by_device.return_value = []
        handler, route_params = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/events/atelier/esp32-001")
        req.route_params = route_params
        handler(req)
        repo.find_by_device.assert_called_once_with(
            "atelier", "esp32-001", limit=DEFAULT_LIMIT,
        )

    def test_custom_limit_forwarded(self):
        repo = MagicMock()
        repo.find_by_device.return_value = []
        handler, route_params = self._setup(repo)

        req = FakeRequest(
            "GET", "/api/iot/events/atelier/esp32-001",
            params={"limit": "5"},
        )
        req.route_params = route_params
        handler(req)
        repo.find_by_device.assert_called_once_with(
            "atelier", "esp32-001", limit=5,
        )

    def test_returns_events_envelope(self):
        repo = MagicMock()
        repo.find_by_device.return_value = [_event_row(id=10)]
        handler, route_params = self._setup(repo)
        req = FakeRequest("GET", "/api/iot/events/atelier/esp32-001")
        req.route_params = route_params
        body = _body_json(handler(req))
        assert "events" in body
        assert body["events"][0]["id"] == 10

    def test_invalid_limit_returns_400(self):
        repo = MagicMock()
        handler, route_params = self._setup(repo)
        req = FakeRequest(
            "GET", "/api/iot/events/atelier/esp32-001",
            params={"limit": "abc"},
        )
        req.route_params = route_params
        resp = handler(req)
        assert resp.status == 400
        repo.find_by_device.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/iot/devices/{site}/{device_id}/count
# ═══════════════════════════════════════════════════════════════════════════


class TestDeviceCountRoute:
    def _setup(self, repo):
        router = Router()
        register_iot_routes(router, repository=repo)
        path = "/api/iot/devices/atelier/esp32-001/count"
        result = router.resolve("GET", path)
        assert result is not None
        return result  # (handler, route_params)

    def test_calls_repo_count_by_device(self):
        repo = MagicMock()
        repo.count_by_device.return_value = 42
        handler, route_params = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/devices/atelier/esp32-001/count")
        req.route_params = route_params
        handler(req)
        repo.count_by_device.assert_called_once_with("atelier", "esp32-001")

    def test_returns_site_device_count_envelope(self):
        repo = MagicMock()
        repo.count_by_device.return_value = 42
        handler, route_params = self._setup(repo)

        req = FakeRequest("GET", "/api/iot/devices/atelier/esp32-001/count")
        req.route_params = route_params
        resp = handler(req)
        assert resp.status == 200
        body = _body_json(resp)
        assert body == {
            "site": "atelier",
            "device_id": "esp32-001",
            "count": 42,
        }

    def test_count_zero(self):
        repo = MagicMock()
        repo.count_by_device.return_value = 0
        handler, route_params = self._setup(repo)
        req = FakeRequest("GET", "/api/iot/devices/atelier/esp32-001/count")
        req.route_params = route_params
        body = _body_json(handler(req))
        assert body["count"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# Erreurs DB → 500 sobre
# ═══════════════════════════════════════════════════════════════════════════


class TestDbErrorReturns500:
    """Une exception côté repository devient une réponse 500 sobre,
    sans fuite SQL/stacktrace côté client."""

    def test_list_events_db_error(self, caplog):
        repo = MagicMock()
        repo.list_recent.side_effect = RuntimeError(
            "SELECT * FROM secret_table — connection lost"
        )
        router = Router()
        register_iot_routes(router, repository=repo)
        handler, _ = router.resolve("GET", "/api/iot/events")

        resp = handler(FakeRequest("GET", "/api/iot/events"))
        assert resp.status == 500
        body = _body_json(resp)
        assert body == {"error": ERROR_INTERNAL}
        # Aucun détail SQL ne fuit dans le body de la réponse.
        body_text = resp.body.decode("utf-8")
        assert "secret_table" not in body_text
        assert "SELECT" not in body_text

    def test_find_by_device_db_error(self):
        repo = MagicMock()
        repo.find_by_device.side_effect = RuntimeError("boom")
        router = Router()
        register_iot_routes(router, repository=repo)
        handler, route_params = router.resolve(
            "GET", "/api/iot/events/atelier/esp32-001",
        )

        req = FakeRequest("GET", "/api/iot/events/atelier/esp32-001")
        req.route_params = route_params
        resp = handler(req)
        assert resp.status == 500
        assert _body_json(resp) == {"error": ERROR_INTERNAL}

    def test_count_by_device_db_error(self):
        repo = MagicMock()
        repo.count_by_device.side_effect = RuntimeError("boom")
        router = Router()
        register_iot_routes(router, repository=repo)
        handler, route_params = router.resolve(
            "GET", "/api/iot/devices/atelier/esp32-001/count",
        )

        req = FakeRequest("GET", "/api/iot/devices/atelier/esp32-001/count")
        req.route_params = route_params
        resp = handler(req)
        assert resp.status == 500
        assert _body_json(resp) == {"error": ERROR_INTERNAL}


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCoreImportsIot:
    """``core/`` continue à ne pas dépendre du module IoT."""

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders


class TestNoSqlInHttpModule:
    """Le contrôleur n'écrit pas de SQL — tout passe par le repository."""

    def test_http_module_has_no_sql_keywords(self):
        text = HTTP_MODULE_FILE.read_text(encoding="utf-8")
        # On exclut les commentaires/docstring : on cherche dans le
        # code Python uniquement les patterns explicites de SQL.
        forbidden = ("SELECT ", "INSERT ", "UPDATE ", "DELETE FROM")
        for marker in forbidden:
            assert marker not in text, (
                f"http.py ne doit pas contenir de SQL ({marker!r})"
            )

    def test_http_module_does_not_import_db(self):
        text = HTTP_MODULE_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in import_lines
            if "core.database" in line or "mariadb" in line
        ]
        assert not offenders, (
            f"http.py ne doit pas importer la base : {offenders}"
        )


class TestPublicApi:
    def test_register_iot_routes_exposed_at_package_root(self):
        import forge_mvc_iot
        assert hasattr(forge_mvc_iot, "register_iot_routes")
        assert "register_iot_routes" in forge_mvc_iot.__all__


class TestControllerDirectUsage:
    """``IotHttpController`` peut aussi être utilisé directement (sans
    passer par ``register_iot_routes``) si l'application veut un
    contrôle plus fin."""

    def test_controller_methods_work_standalone(self):
        repo = MagicMock()
        repo.list_recent.return_value = []
        controller = IotHttpController(repo)
        resp = controller.list_events(FakeRequest("GET", "/api/iot/events"))
        assert resp.status == 200
        assert _body_json(resp) == {"events": []}
