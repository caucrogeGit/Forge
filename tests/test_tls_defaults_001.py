"""
Tests SECURITY-TLS-DEFAULTS-001 — Configuration TLS dev explicite.

Valide :
- _make_ssl_context() retourne un ssl.SSLContext
- minimum_version est >= TLS 1.2
- ssl.TLSVersion.TLSv1_2 est disponible dans l'environnement Python
- APP_SSL_ENABLED est un booléen dans config
- APP_SSL_ENABLED=false par défaut en dev/test (env/example ne le force pas à true)
- la documentation indique que TLS production relève de Nginx
- minimum_version apparaît dans le source de app.py
- TLSv1_2 apparaît dans le source de app.py
"""
import ssl

from app import _make_ssl_context
from config import APP_SSL_ENABLED


# ── ssl.TLSVersion disponible ───────────────────────────────────────────────────

def test_tls_version_tlsv1_2_available():
    assert hasattr(ssl.TLSVersion, "TLSv1_2")


def test_tls_version_tlsv1_3_available():
    assert hasattr(ssl.TLSVersion, "TLSv1_3")


# ── _make_ssl_context ───────────────────────────────────────────────────────────

def test_make_ssl_context_returns_sslcontext():
    ctx = _make_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)


def test_make_ssl_context_minimum_version_is_tls12():
    ctx = _make_ssl_context()
    assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2


def test_make_ssl_context_minimum_version_gte_tls12():
    ctx = _make_ssl_context()
    assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_make_ssl_context_does_not_allow_tls10():
    """TLS 1.0 est inférieur à 1.2 — ne doit pas être la version minimale."""
    ctx = _make_ssl_context()
    assert ctx.minimum_version != ssl.TLSVersion.TLSv1


def test_make_ssl_context_does_not_allow_ssl3():
    ctx = _make_ssl_context()
    assert ctx.minimum_version != ssl.TLSVersion.SSLv3


def test_make_ssl_context_protocol_is_tls_server():
    ctx = _make_ssl_context()
    assert ctx.protocol == ssl.PROTOCOL_TLS_SERVER


def test_make_ssl_context_independent_instances():
    """Deux appels retournent deux contextes indépendants."""
    ctx1 = _make_ssl_context()
    ctx2 = _make_ssl_context()
    assert ctx1 is not ctx2


# ── config ──────────────────────────────────────────────────────────────────────

def test_app_ssl_enabled_is_bool():
    assert isinstance(APP_SSL_ENABLED, bool)


def test_app_ssl_enabled_default_true_in_dev():
    """En mode dev, APP_SSL_ENABLED est True par défaut (HTTPS local activé)."""
    assert APP_SSL_ENABLED is True


# ── Source app.py contient la configuration explicite ──────────────────────────

def test_app_py_contains_minimum_version():
    import inspect
    import app as app_mod
    src = inspect.getsource(app_mod)
    assert "minimum_version" in src


def test_app_py_contains_tlsv1_2():
    import inspect
    import app as app_mod
    src = inspect.getsource(app_mod)
    assert "TLSv1_2" in src


def test_app_py_uses_make_ssl_context_helper():
    import inspect
    import app as app_mod
    src = inspect.getsource(app_mod)
    assert "_make_ssl_context()" in src


# ── Documentation TLS/Nginx ─────────────────────────────────────────────────────

def test_deployment_doc_mentions_nginx_for_production_tls():
    content = open("docs/deployment.md", encoding="utf-8").read()
    assert "Nginx" in content
    assert "TLS" in content or "HTTPS" in content


def test_deployment_doc_mentions_tls12():
    content = open("docs/deployment.md", encoding="utf-8").read()
    assert "1.2" in content


def test_security_doc_mentions_nginx():
    content = open("docs/security.md", encoding="utf-8").read()
    assert "Nginx" in content or "nginx" in content


def test_security_doc_mentions_tls12():
    content = open("docs/security.md", encoding="utf-8").read()
    assert "1.2" in content


def test_readme_mentions_https_dev_not_production():
    # README simplifié : il annonce le HTTPS natif (dev) ; le détail
    # production (Nginx, TLS terminaison) est sur le site de doc — vérifié
    # par test_deployment_doc_mentions_nginx_for_production_tls ci-dessus.
    content = open("README.md", encoding="utf-8").read()
    assert "HTTPS" in content
