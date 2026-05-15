"""
Tests SECURITY-CSP-NONCE-001 — Nonce CSP optionnel par requête.

Valide :
- generate_nonce() produit un nonce URL-safe non vide
- set/get_request_nonce fonctionne en thread-local
- Isolation entre threads (nonces distincts par thread)
- build_csp_header() sans nonce → script-src 'self' uniquement
- build_csp_header() avec nonce → 'nonce-<valeur>' inclus, pas unsafe-inline
- csp_nonce() Jinja retourne "" quand aucun nonce n'est posé
- csp_nonce() Jinja retourne le nonce quand il est posé
- APP_CSP_NONCE_ENABLED est bien un booléen dans config
- Le module csp n'utilise pas de sérialiseurs dangereux
"""
import threading

from core.security.csp import (
    build_csp_header,
    generate_nonce,
    get_request_nonce,
    set_request_nonce,
)


# ── generate_nonce ──────────────────────────────────────────────────────────────

def test_generate_nonce_returns_nonempty_string():
    nonce = generate_nonce()
    assert isinstance(nonce, str)
    assert len(nonce) > 0


def test_generate_nonce_is_url_safe():
    nonce = generate_nonce()
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
    assert all(c in allowed for c in nonce)


def test_generate_nonce_unique():
    nonces = {generate_nonce() for _ in range(20)}
    assert len(nonces) == 20


def test_generate_nonce_min_entropy():
    nonce = generate_nonce()
    # secrets.token_urlsafe(16) → 22 chars minimum
    assert len(nonce) >= 16


# ── set/get_request_nonce ───────────────────────────────────────────────────────

def test_set_get_nonce_roundtrip():
    nonce = generate_nonce()
    set_request_nonce(nonce)
    assert get_request_nonce() == nonce


def test_set_none_clears_nonce():
    set_request_nonce("something")
    set_request_nonce(None)
    assert get_request_nonce() is None


def test_get_nonce_default_is_none():
    import core.security.csp as csp_mod
    # Réinitialise le stockage thread-local pour ce thread
    if hasattr(csp_mod._local, "nonce"):
        del csp_mod._local.nonce
    assert get_request_nonce() is None


def test_nonce_isolation_between_threads():
    """Deux threads ont des nonces indépendants."""
    results = {}

    def worker(name, value):
        set_request_nonce(value)
        threading.Event().wait(0.01)  # laisse l'autre thread tourner
        results[name] = get_request_nonce()

    t1 = threading.Thread(target=worker, args=("t1", "nonce-thread-1"))
    t2 = threading.Thread(target=worker, args=("t2", "nonce-thread-2"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1"] == "nonce-thread-1"
    assert results["t2"] == "nonce-thread-2"


# ── build_csp_header ────────────────────────────────────────────────────────────

def test_build_csp_no_nonce_contains_script_src_self():
    header = build_csp_header(None)
    assert "script-src 'self'" in header


def test_build_csp_no_nonce_no_unsafe_inline():
    header = build_csp_header(None)
    assert "unsafe-inline" not in header


def test_build_csp_no_nonce_no_nonce_directive():
    header = build_csp_header(None)
    assert "nonce-" not in header


def test_build_csp_with_nonce_contains_nonce():
    header = build_csp_header("abc123")
    assert "'nonce-abc123'" in header


def test_build_csp_with_nonce_retains_script_src_self():
    header = build_csp_header("abc123")
    assert "script-src 'self'" in header


def test_build_csp_with_nonce_no_unsafe_inline():
    header = build_csp_header("abc123")
    assert "unsafe-inline" not in header


def test_build_csp_with_nonce_contains_default_src():
    header = build_csp_header("xyz")
    assert "default-src 'self'" in header


def test_build_csp_with_nonce_contains_frame_ancestors():
    header = build_csp_header("xyz")
    assert "frame-ancestors 'none'" in header


def test_build_csp_default_arg_is_none():
    header_explicit = build_csp_header(None)
    header_default = build_csp_header()
    assert header_explicit == header_default


def test_build_csp_empty_string_nonce_treated_as_no_nonce():
    header = build_csp_header("")
    assert "nonce-" not in header
    assert "unsafe-inline" not in header


# ── Jinja helper csp_nonce() ────────────────────────────────────────────────────

def test_jinja_csp_nonce_returns_empty_when_no_nonce():
    from integrations.jinja2.renderer import _csp_nonce
    set_request_nonce(None)
    assert _csp_nonce() == ""


def test_jinja_csp_nonce_returns_nonce_when_set():
    from integrations.jinja2.renderer import _csp_nonce
    set_request_nonce("test-nonce-value")
    result = _csp_nonce()
    assert result == "test-nonce-value"
    set_request_nonce(None)


def test_jinja_csp_nonce_is_string():
    from integrations.jinja2.renderer import _csp_nonce
    set_request_nonce(None)
    assert isinstance(_csp_nonce(), str)


def test_jinja_renderer_has_csp_nonce_global():
    from integrations.jinja2.renderer import Jinja2Renderer
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        renderer = Jinja2Renderer(tmp)
        assert "csp_nonce" in renderer._env.globals
        assert callable(renderer._env.globals["csp_nonce"])


# ── config ──────────────────────────────────────────────────────────────────────

def test_app_csp_nonce_enabled_is_bool():
    from config import APP_CSP_NONCE_ENABLED
    assert isinstance(APP_CSP_NONCE_ENABLED, bool)


def test_app_csp_nonce_enabled_default_is_false():
    """Par défaut (env/example), APP_CSP_NONCE_ENABLED=false."""
    from config import APP_CSP_NONCE_ENABLED
    assert APP_CSP_NONCE_ENABLED is False


# ── Absence de sérialiseurs dangereux ───────────────────────────────────────────

_BANNED = ["pic" + "kle", "mar" + "shal", "ev" + "al(", "ex" + "ec("]


def test_banned_serializers_absent_from_csp_module():
    import inspect
    import core.security.csp as csp_mod
    src = inspect.getsource(csp_mod)
    for banned in _BANNED:
        assert banned not in src, f"Trouvé '{banned}' dans csp.py"


def test_banned_serializers_absent_from_this_test():
    import inspect
    import tests.test_csp_nonce_001 as this_mod
    src = inspect.getsource(this_mod)
    for banned in _BANNED:
        assert src.count(banned) <= 1, f"'{banned}' apparaît hors de _BANNED"
