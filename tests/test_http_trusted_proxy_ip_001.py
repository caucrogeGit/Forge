"""Tests — HTTP-TRUSTED-PROXY-IP-001.

Verrouille la résolution de l'IP client : `X-Real-IP` n'est honoré que
lorsque l'adresse distante figure dans la liste explicite des proxies de
confiance. Tout autre cas (proxy non listé, header manquant, header
invalide) doit retomber sur l'adresse observée par le socket.
"""
from __future__ import annotations

from io import BytesIO

import pytest

import core.forge as forge
from core.http.request import Request, resolve_client_ip


class _Headers:
    """Mime `http.client.HTTPMessage.get(name, default)` — insensible à la casse."""

    def __init__(self, mapping=None):
        self._lower = {k.lower(): v for k, v in (mapping or {}).items()}

    def get(self, name, default=""):
        return self._lower.get(name.lower(), default)


# ── Fonction pure : resolve_client_ip ────────────────────────────────────────


class TestResolveClientIpRules:
    def test_no_trusted_proxies_ignores_real_ip(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"X-Real-IP": "203.0.113.42"}),
            frozenset(),
        )
        assert ip == "127.0.0.1"

    def test_trusted_proxy_with_valid_real_ip_uses_it(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"X-Real-IP": "203.0.113.42"}),
            {"127.0.0.1"},
        )
        assert ip == "203.0.113.42"

    def test_untrusted_proxy_ignores_real_ip(self):
        ip = resolve_client_ip(
            "198.51.100.10",
            _Headers({"X-Real-IP": "203.0.113.42"}),
            {"127.0.0.1"},
        )
        assert ip == "198.51.100.10"

    def test_invalid_real_ip_falls_back(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"X-Real-IP": "not-an-ip"}),
            {"127.0.0.1"},
        )
        assert ip == "127.0.0.1"

    def test_missing_real_ip_falls_back(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({}),
            {"127.0.0.1"},
        )
        assert ip == "127.0.0.1"

    def test_empty_real_ip_falls_back(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"X-Real-IP": "   "}),
            {"127.0.0.1"},
        )
        assert ip == "127.0.0.1"

    @pytest.mark.parametrize("real_ip", ["203.0.113.42", "2001:db8::1"])
    def test_accepts_ipv4_and_ipv6(self, real_ip):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"X-Real-IP": real_ip}),
            {"127.0.0.1"},
        )
        assert ip == real_ip

    def test_ipv6_loopback_can_be_trusted(self):
        ip = resolve_client_ip(
            "::1",
            _Headers({"X-Real-IP": "203.0.113.42"}),
            {"::1"},
        )
        assert ip == "203.0.113.42"

    def test_zero_dot_zero_is_not_a_wildcard(self):
        # 0.0.0.0 ne vaut que pour lui-même — pas de confiance générique.
        ip = resolve_client_ip(
            "203.0.113.42",
            _Headers({"X-Real-IP": "10.0.0.1"}),
            {"0.0.0.0"},
        )
        assert ip == "203.0.113.42"

    def test_header_name_is_case_insensitive(self):
        ip = resolve_client_ip(
            "127.0.0.1",
            _Headers({"x-real-ip": "203.0.113.42"}),
            {"127.0.0.1"},
        )
        assert ip == "203.0.113.42"


# ── Config parsing (APP_TRUSTED_PROXIES) ────────────────────────────────────


class TestConfigParsing:
    def test_tolerates_spaces(self, monkeypatch):
        monkeypatch.setenv("APP_TRUSTED_PROXIES", "127.0.0.1, ::1 , 192.168.1.10")
        # Recharge config.py pour relire l'env.
        import importlib
        import config
        importlib.reload(config)
        assert config.APP_TRUSTED_PROXIES == frozenset(
            {"127.0.0.1", "::1", "192.168.1.10"}
        )

    def test_empty_value_is_empty_set(self, monkeypatch):
        monkeypatch.setenv("APP_TRUSTED_PROXIES", "")
        import importlib
        import config
        importlib.reload(config)
        assert config.APP_TRUSTED_PROXIES == frozenset()


# ── Intégration : Request lit la config et résout correctement ──────────────


class _Handler:
    def __init__(self, path="/", method="GET", remote="127.0.0.1", headers=None,
                 body=b""):
        self.path = path
        self.command = method
        self.headers = _Headers(headers)
        self.client_address = (remote, 0)
        self.rfile = BytesIO(body)


@pytest.fixture
def trusted_proxies():
    """Restaure la config trusted_proxies après chaque test."""
    previous = forge.get("trusted_proxies")
    yield
    forge.configure(trusted_proxies=previous)


class TestRequestIntegration:
    def test_unchanged_without_proxy(self, trusted_proxies):
        forge.configure(trusted_proxies=frozenset())
        req = Request(_Handler(remote="198.51.100.10"))
        assert req.ip == "198.51.100.10"

    def test_real_ip_used_behind_trusted_proxy(self, trusted_proxies):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        req = Request(_Handler(
            remote="127.0.0.1",
            headers={"X-Real-IP": "203.0.113.42"},
        ))
        assert req.ip == "203.0.113.42"

    def test_real_ip_ignored_when_proxy_untrusted(self, trusted_proxies):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        req = Request(_Handler(
            remote="198.51.100.10",
            headers={"X-Real-IP": "203.0.113.42"},
        ))
        assert req.ip == "198.51.100.10"

    def test_invalid_real_ip_falls_back_in_request(self, trusted_proxies):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        req = Request(_Handler(
            remote="127.0.0.1",
            headers={"X-Real-IP": "bogus"},
        ))
        assert req.ip == "127.0.0.1"
