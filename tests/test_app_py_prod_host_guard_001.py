"""Tests — APP-PY-PROD-HOST-GUARD-001.

Verrouille que `python app.py` refuse de démarrer en `APP_ENV=prod` quand
`APP_HOST` cible une interface publique (`0.0.0.0`, `::`, `[::]`), tout
en laissant fonctionner :

  * `python app.py` en dev / test / staging (même sur `0.0.0.0`) ;
  * `python app.py` en prod sur loopback (`127.0.0.1`, `localhost`, `::1`) ;
  * la production WSGI (`core.wsgi.create_configured_wsgi_app`).

Tests directs sur les fonctions pures de `core/dev_server.py` — pas besoin
de spawn un serveur. Un test E2E vérifie en plus le chemin réel via
``subprocess`` pour prouver que le garde fait exiter le processus avec
un code non nul et un message clair sur stderr/stdout.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from core.dev_server import (
    format_prod_host_guard_error,
    is_dangerous_public_host,
    should_block_prod_public_host,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Détection des hôtes publics dangereux
# ---------------------------------------------------------------------------


class TestIsDangerousPublicHost:
    @pytest.mark.parametrize("host", [
        "0.0.0.0",
        "::",
        "[::]",                # forme bracketed URL-style
        "  0.0.0.0  ",         # whitespace bordure
        "::",                  # bis pour confirmer
        "[::]  ",              # whitespace + bracket
        "0.0.0.0\n",           # newline parasite venant d'un .env mal édité
    ])
    def test_dangerous_hosts_are_recognized(self, host):
        assert is_dangerous_public_host(host), (
            f"{host!r} doit être détecté comme hôte public dangereux."
        )

    @pytest.mark.parametrize("host", [
        "127.0.0.1",
        "localhost",
        "::1",
        "[::1]",
        "LOCALHOST",            # casse différente
        "  127.0.0.1  ",
        "10.0.0.5",             # IP privée spécifique — OK (l'utilisateur sait ce qu'il fait)
        "192.168.1.10",
        "example.com",
        "",                     # vide — pas explicitement dangereux
        None,                   # None — None.strip() doit être géré
    ])
    def test_safe_hosts_are_not_blocked(self, host):
        assert not is_dangerous_public_host(host), (
            f"{host!r} doit rester autorisé (pas un host public dangereux)."
        )


# ---------------------------------------------------------------------------
# Combinaison (env, host)
# ---------------------------------------------------------------------------


class TestShouldBlockProdPublicHost:
    """La règle exacte : `APP_ENV=prod` ET hôte public → bloqué."""

    @pytest.mark.parametrize("host", ["0.0.0.0", "::", "[::]"])
    def test_prod_plus_public_host_is_blocked(self, host):
        assert should_block_prod_public_host("prod", host) is True

    @pytest.mark.parametrize("env", ["PROD", "Prod", "  prod  ", "prod\n"])
    def test_prod_env_is_case_and_whitespace_insensitive(self, env):
        assert should_block_prod_public_host(env, "0.0.0.0") is True

    @pytest.mark.parametrize("host", [
        "127.0.0.1", "localhost", "::1", "[::1]", "10.0.0.5",
    ])
    def test_prod_plus_local_host_is_allowed(self, host):
        assert should_block_prod_public_host("prod", host) is False, (
            "Les hôtes locaux/spécifiques doivent rester autorisés même en prod."
        )

    @pytest.mark.parametrize("env", ["dev", "test", "staging", "preprod"])
    @pytest.mark.parametrize("host", ["0.0.0.0", "::", "[::]"])
    def test_non_prod_env_allows_public_host(self, env, host):
        assert should_block_prod_public_host(env, host) is False, (
            f"En APP_ENV={env}, APP_HOST={host} doit rester autorisé."
        )


# ---------------------------------------------------------------------------
# Message d'erreur — contenu obligatoire
# ---------------------------------------------------------------------------


class TestErrorMessageContent:
    """Le message doit être actionnable et survivre à toute reformulation."""

    @pytest.fixture
    def message(self):
        return format_prod_host_guard_error("prod", "0.0.0.0")

    def test_mentions_python_app_py(self, message):
        assert "python app.py" in message

    def test_mentions_production(self, message):
        assert "production" in message.lower()

    def test_mentions_app_host(self, message):
        assert "APP_HOST" in message

    def test_mentions_wsgi(self, message):
        assert "WSGI" in message

    def test_mentions_gunicorn(self, message):
        assert "Gunicorn" in message.lower() or "gunicorn" in message.lower()

    def test_mentions_reverse_proxy(self, message):
        assert "reverse proxy" in message.lower()

    def test_echoes_provided_values(self, message):
        # Le message inclut les valeurs réelles pour faciliter le diagnostic.
        assert "'prod'" in message
        assert "'0.0.0.0'" in message

    def test_points_to_wsgi_deployment_doc(self, message):
        assert "docs/deployment/wsgi-deployment.md" in message

    def test_offers_local_workaround(self, message):
        # Donne une issue de secours : limiter APP_HOST à 127.0.0.1.
        assert "127.0.0.1" in message


# ---------------------------------------------------------------------------
# Le chemin WSGI ne doit JAMAIS être affecté
# ---------------------------------------------------------------------------


class TestWsgiPathNotBlocked:
    """`create_configured_wsgi_app` n'appelle pas le garde — la production
    WSGI/Gunicorn doit rester fonctionnelle même avec `APP_ENV=prod` et
    `APP_HOST=0.0.0.0` dans l'environnement."""

    def test_wsgi_module_does_not_call_the_guard(self):
        import core.wsgi as wsgi
        from pathlib import Path
        source = Path(wsgi.__file__).read_text(encoding="utf-8")
        assert "should_block_prod_public_host" not in source, (
            "core/wsgi.py ne doit PAS appeler le garde — le chemin WSGI est "
            "indépendant de APP_HOST (c'est Gunicorn / le reverse proxy qui "
            "décide où écouter)."
        )
        assert "format_prod_host_guard_error" not in source

    def test_app_py_calls_guard_only_under_main(self):
        """Le garde doit être appelé DANS le bloc `if __name__ == "__main__":`,
        sinon importer app.py (depuis un test ou un wsgi.py) le déclencherait."""
        source = (_REPO_ROOT / "app.py").read_text(encoding="utf-8")
        idx_main = source.find('if __name__ == "__main__":')
        idx_guard = source.find("should_block_prod_public_host(APP_ENV, APP_HOST)")
        assert idx_main != -1, "Le bloc `if __name__ == '__main__':` est introuvable."
        assert idx_guard != -1, "Le garde n'est pas appelé dans app.py."
        assert idx_guard > idx_main, (
            "Le garde doit être appelé DANS le bloc `if __name__ == '__main__':` "
            "— sinon un simple import de app.py le déclencherait."
        )


# ---------------------------------------------------------------------------
# E2E — `python app.py` réellement bloqué en prod public
# ---------------------------------------------------------------------------
#
# Sur Forge, ``config.py`` appelle ``load_dotenv("env/prod", override=True)``
# qui écrase la variable ``APP_HOST`` injectée par le sous-processus si le
# fichier ``env/prod`` la définit. On contourne en écrivant un ``env/prod``
# temporaire (puis on restaure) — c'est intrusif sur le tree mais nécessaire
# pour prouver l'enchaînement complet.


@pytest.fixture
def env_prod_with_public_host():
    """Pose `APP_HOST=0.0.0.0` dans `env/prod`, yield, puis restaure.

    `env/prod` est gitignoré : sur un checkout propre (CI), il est absent. On
    le synthétise alors à partir de `env/example` (toujours commité, donc
    présent partout) — qui contient toutes les clés que `config.py` lit à
    l'import — et on le supprime au teardown. Le test reste ainsi autonome,
    sans dépendre d'un `env/prod` local ni laisser de trace sur le tree.
    """
    env_prod_file = _REPO_ROOT / "env" / "prod"
    existed = env_prod_file.exists()
    if existed:
        original = env_prod_file.read_text(encoding="utf-8")
    else:
        original = (_REPO_ROOT / "env" / "example").read_text(encoding="utf-8")
    try:
        # Réécriture : on retire la ligne APP_HOST existante et on injecte 0.0.0.0.
        new_lines = [
            line for line in original.splitlines()
            if not line.startswith("APP_HOST=")
        ]
        new_lines.append("APP_HOST=0.0.0.0  # injecté par test APP-PY-PROD-HOST-GUARD-001")
        env_prod_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        yield
    finally:
        # Restauration inconditionnelle : restaurer le contenu si le fichier
        # préexistait, sinon le supprimer (checkout propre / CI).
        if existed:
            env_prod_file.write_text(original, encoding="utf-8")
        else:
            env_prod_file.unlink(missing_ok=True)


class TestEndToEndAppPyRefusesToStart:
    """Spawn `python app.py` avec env/prod modifié pour exposer 0.0.0.0,
    et vérifie qu'il exite avec un message de garde clair, sans démarrer
    de serveur."""

    def _run_app_py(self, *, timeout: float = 6.0) -> subprocess.CompletedProcess:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),
            "APP_ENV": "prod",
            "FORGE_MFA_SECRET_KEY": "test-key-placeholder-not-used",
        }
        return subprocess.run(
            [sys.executable, str(_REPO_ROOT / "app.py")],
            cwd=str(_REPO_ROOT),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )

    def test_prod_plus_0_0_0_0_exits_with_guard_message(
        self, env_prod_with_public_host
    ):
        try:
            result = self._run_app_py()
        except subprocess.TimeoutExpired:
            pytest.fail(
                "python app.py n'a pas exité en moins de 6s — le garde ne "
                "fonctionne pas (le serveur a démarré sur 0.0.0.0 en prod)."
            )
        assert result.returncode != 0, (
            f"python app.py devait exiter avec un code != 0, reçu "
            f"{result.returncode}. stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        combined = result.stdout + result.stderr
        # Le message de garde DOIT apparaître. On vérifie un marqueur unique
        # qui ne peut venir QUE de `format_prod_host_guard_error` — pas
        # d'autres messages d'erreur Forge.
        assert "Refus de démarrer `python app.py`" in combined, (
            f"Le message du garde prod-host est absent. Sortie complète :\n"
            f"{combined}"
        )
        assert "WSGI" in combined
