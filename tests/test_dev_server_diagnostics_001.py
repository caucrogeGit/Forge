"""
Tests du ticket DEV-SERVER-DIAGNOSTICS-001.

Couvre les fonctions pures de mise en forme des messages affichés par app.py
au démarrage du serveur de développement. Les fonctions vivent dans
core/app/dev_server.py pour être testables sans déclencher les effets de bord
d'import de app.py.
"""
import pytest

from core.app.dev_server import (
    format_port_in_use_message,
    format_startup_messages,
    scheme_for,
)


class TestSchemeFor:
    def test_https_when_ssl_enabled(self):
        assert scheme_for(True) == "https"

    def test_http_when_ssl_disabled(self):
        assert scheme_for(False) == "http"


class TestFormatStartupMessages:
    def test_first_line_keeps_historical_format_http(self):
        lines = format_startup_messages("127.0.0.1", 8000, ssl_enabled=False)
        assert lines[0] == "Serveur en écoute sur http://127.0.0.1:8000"

    def test_first_line_keeps_historical_format_https(self):
        lines = format_startup_messages("127.0.0.1", 8000, ssl_enabled=True)
        assert lines[0] == "Serveur en écoute sur https://127.0.0.1:8000"

    def test_no_zero_host_help_when_host_is_loopback(self):
        lines = format_startup_messages("127.0.0.1", 8000, ssl_enabled=False)
        joined = "\n".join(lines)
        assert "0.0.0.0" not in joined
        assert "<IP_MACHINE>" not in joined

    def test_zero_host_emits_loopback_and_network_hints(self):
        lines = format_startup_messages("0.0.0.0", 8000, ssl_enabled=False)
        joined = "\n".join(lines)
        assert "http://127.0.0.1:8000" in joined
        assert "<IP_MACHINE>" in joined
        assert "toutes les interfaces" in joined

    def test_zero_host_uses_https_scheme_in_hints_when_ssl(self):
        lines = format_startup_messages("0.0.0.0", 8000, ssl_enabled=True)
        joined = "\n".join(lines)
        assert "https://127.0.0.1:8000" in joined
        assert "https://<IP_MACHINE>:8000" in joined

    def test_https_warning_emitted_only_when_ssl_enabled(self):
        with_ssl    = "\n".join(format_startup_messages("127.0.0.1", 8000, True))
        without_ssl = "\n".join(format_startup_messages("127.0.0.1", 8000, False))
        assert "HTTPS" in with_ssl
        assert "HTTPS" not in without_ssl

    @pytest.mark.parametrize("port", [80, 8000, 8443, 65535])
    def test_port_appears_in_first_line(self, port):
        lines = format_startup_messages("0.0.0.0", port, ssl_enabled=False)
        assert f":{port}" in lines[0]


class TestFormatPortInUseMessage:
    def test_mentions_port_and_host(self):
        msg = format_port_in_use_message("0.0.0.0", 8000)
        assert "8000" in msg
        assert "0.0.0.0" in msg

    def test_proposes_diagnostic_commands(self):
        msg = format_port_in_use_message("0.0.0.0", 8000)
        assert "ss -tulpn | grep :8000" in msg
        assert "lsof -i :8000" in msg

    def test_proposes_solutions(self):
        msg = format_port_in_use_message("0.0.0.0", 8000)
        assert "APP_PORT" in msg
        assert "python app.py" in msg

    def test_states_no_server_was_started(self):
        msg = format_port_in_use_message("0.0.0.0", 8000)
        assert "Aucun serveur Forge n'a été démarré." in msg

    def test_does_not_propose_killing_existing_process(self):
        msg = format_port_in_use_message("0.0.0.0", 8000).lower()
        for forbidden in ("kill -9", "pkill", "killall"):
            assert forbidden not in msg

    @pytest.mark.parametrize("port", [80, 8000, 8443])
    def test_port_consistently_substituted(self, port):
        msg = format_port_in_use_message("127.0.0.1", port)
        assert f":{port}" in msg
        assert f"port {port}" in msg
