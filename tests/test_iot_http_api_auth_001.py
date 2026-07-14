"""Tests de la protection Bearer token de l'API HTTP IoT — IOT-HTTP-API-AUTH-001.

L'API IoT est ouverte par défaut (parcours local/pédagogique). Si
``FORGE_IOT_API_TOKEN`` est défini (``IotConfig.api_token``), les trois
routes exigent ``Authorization: Bearer <token>``.

Vérifie :
- sans token configuré → API accessible ;
- token configuré + pas de header / mauvais schéma / mauvais token → 401 ;
- token configuré + bon token → le repository est appelé ;
- le token ne fuit ni dans ``repr(IotConfig)`` ni dans les réponses JSON ;
- ``secrets.compare_digest`` est utilisé ;
- les trois routes sont protégées ;
- ``core/`` n'importe pas ``forge_mvc_iot``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.http.router import Router

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.http import (
    IotHttpController,
    register_iot_routes,
)
from forge_mvc_testing import FakeRequest

PROJECT_ROOT = Path(__file__).parent.parent
HTTP_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot" / "http.py"
)
CORE_DIR = PROJECT_ROOT / "core"

TOKEN = "supersecret-token-xyz"


# ── Helpers / fakes ──────────────────────────────────────────────────────────


def _config(api_token=None) -> IotConfig:
    return IotConfig(
        mqtt_host="localhost", mqtt_port=1883,
        mqtt_topic="forge/+/+/telemetry", mqtt_client_id="forge-iot",
        mqtt_username=None, mqtt_password=None, api_token=api_token,
    )


class _FakeRepo:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def list_recent(self, *, limit=100):
        self.calls.append(("list_recent", limit))
        return []

    def find_by_device(self, site, device_id, *, limit=100):
        self.calls.append(("find_by_device", site, device_id, limit))
        return []

    def count_by_device(self, site, device_id):
        self.calls.append(("count_by_device", site, device_id))
        return 0


def _controller(api_token=None):
    repo = _FakeRepo()
    return IotHttpController(repo, api_token=api_token), repo


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _body(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


# Les trois handlers, avec une requête qui porte les route_params requis.
def _request_for(handler_name: str, headers=None) -> FakeRequest:
    req = FakeRequest("GET", "/api/iot/events", headers=headers)
    if handler_name != "list_events":
        req.route_params = {"site": "atelier", "device_id": "esp32-001"}
    return req


HANDLERS = ["list_events", "find_by_device", "count_by_device"]


# ═══════════════════════════════════════════════════════════════════════════
# API ouverte quand aucun token n'est configuré
# ═══════════════════════════════════════════════════════════════════════════


class TestOpenWhenNoToken:
    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_no_token_means_open(self, handler_name):
        controller, repo = _controller(api_token=None)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name))
        assert resp.status == 200
        assert repo.calls, "le repository doit être appelé quand l'API est ouverte"


# ═══════════════════════════════════════════════════════════════════════════
# Token configuré → 401 sans/avec mauvais credentials
# ═══════════════════════════════════════════════════════════════════════════


class TestUnauthorized:
    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_missing_header_yields_401(self, handler_name):
        controller, repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name))
        assert resp.status == 401
        assert _body(resp) == {"error": "unauthorized"}
        assert repo.calls == [], "le repository ne doit PAS être appelé"

    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_wrong_scheme_yields_401(self, handler_name):
        controller, repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        headers = {"Authorization": f"Basic {TOKEN}"}
        resp = handler(_request_for(handler_name, headers=headers))
        assert resp.status == 401
        assert repo.calls == []

    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_wrong_token_yields_401(self, handler_name):
        controller, repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name, headers=_bearer("mauvais")))
        assert resp.status == 401
        assert repo.calls == []

    def test_empty_bearer_yields_401(self):
        controller, repo = _controller(api_token=TOKEN)
        resp = controller.list_events(
            _request_for("list_events", headers={"Authorization": "Bearer "})
        )
        assert resp.status == 401
        assert repo.calls == []


# ═══════════════════════════════════════════════════════════════════════════
# Token configuré + bon token → repository appelé
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorized:
    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_good_token_calls_repository(self, handler_name):
        controller, repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name, headers=_bearer(TOKEN)))
        assert resp.status == 200
        assert repo.calls, "le repository doit être appelé avec le bon token"


# ═══════════════════════════════════════════════════════════════════════════
# Enregistrement : register_iot_routes propage le token de la config
# ═══════════════════════════════════════════════════════════════════════════


class TestRegistrationWiresToken:
    def test_register_with_token_protects_routes(self):
        repo = _FakeRepo()
        router = Router()
        register_iot_routes(router, repository=repo, config=_config(api_token=TOKEN))
        handler, _params = router.resolve("GET", "/api/iot/events")
        # Sans header → 401.
        assert handler(FakeRequest("GET", "/api/iot/events")).status == 401
        assert repo.calls == []
        # Avec le bon token → 200 + repo appelé.
        ok = handler(FakeRequest("GET", "/api/iot/events", headers=_bearer(TOKEN)))
        assert ok.status == 200
        assert repo.calls

    def test_register_without_token_stays_open(self):
        repo = _FakeRepo()
        router = Router()
        register_iot_routes(router, repository=repo, config=_config(api_token=None))
        handler, _params = router.resolve("GET", "/api/iot/events")
        assert handler(FakeRequest("GET", "/api/iot/events")).status == 200
        assert repo.calls


# ═══════════════════════════════════════════════════════════════════════════
# Non-fuite du token
# ═══════════════════════════════════════════════════════════════════════════


class TestTokenNeverLeaks:
    def test_token_absent_from_repr(self):
        assert TOKEN not in repr(_config(api_token=TOKEN))

    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_token_absent_from_401_body(self, handler_name):
        controller, _repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name, headers=_bearer("mauvais")))
        assert TOKEN not in resp.body.decode("utf-8")

    @pytest.mark.parametrize("handler_name", HANDLERS)
    def test_token_absent_from_authorized_body(self, handler_name):
        controller, _repo = _controller(api_token=TOKEN)
        handler = getattr(controller, handler_name)
        resp = handler(_request_for(handler_name, headers=_bearer(TOKEN)))
        assert TOKEN not in resp.body.decode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous
# ═══════════════════════════════════════════════════════════════════════════


class TestImplementationGuards:
    def test_delegue_a_la_primitive_bearer_du_coeur(self):
        # CORE-HTTP-BEARER-PRIMITIVE-001 : la logique Bearer (comparaison temps
        # constant incluse) a quitté ce module pour core/http/bearer.py, testé
        # une fois pour tous. iot doit déléguer à la primitive.
        src = HTTP_FILE.read_text(encoding="utf-8")
        assert "is_bearer_authorized" in src, (
            "iot doit autoriser via core.http.bearer.is_bearer_authorized "
            "(primitive partagée), pas sa propre copie."
        )
        bearer = (PROJECT_ROOT / "core" / "http" / "bearer.py").read_text(encoding="utf-8")
        assert "secrets.compare_digest" in bearer, (
            "la primitive Bearer du cœur doit comparer le token en temps constant."
        )

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders
