"""Tests CSP-NONCE-SCOPE-001 — le nonce CSP est remis à zéro en fin de requête.

Le nonce est thread-local et les threads sont réutilisés (serveur de dev). Le
gestionnaire de contexte request_nonce() doit garantir qu'aucun nonce ne fuit
vers une requête suivante sur le même thread.
"""

import threading

from core.security.csp import (
    build_csp_header,
    clear_request_nonce,
    generate_nonce,
    get_request_nonce,
    request_nonce,
)


def test_request_nonce_sets_then_resets():
    clear_request_nonce()
    assert get_request_nonce() is None
    with request_nonce("abc123") as n:
        assert n == "abc123"
        assert get_request_nonce() == "abc123"
    assert get_request_nonce() is None, "le nonce doit être remis à zéro en sortie"


def test_request_nonce_resets_even_on_exception():
    clear_request_nonce()
    try:
        with request_nonce("xyz"):
            raise ValueError("boom")
    except ValueError:
        pass
    assert get_request_nonce() is None, "remise à zéro garantie même sur exception"


def test_no_leak_between_simulated_requests_same_thread():
    # Première requête pose un nonce ; la seconde n'en pose pas et ne doit
    # surtout pas hériter de celui de la première.
    with request_nonce(generate_nonce()):
        pass
    assert get_request_nonce() is None
    # requête suivante sans nonce
    assert build_csp_header(get_request_nonce()) == build_csp_header(None)
    assert "nonce-" not in build_csp_header(get_request_nonce())


def test_thread_local_isolation():
    clear_request_nonce()
    seen = {}

    def worker():
        with request_nonce("thread-nonce"):
            seen["inside"] = get_request_nonce()

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    assert seen["inside"] == "thread-nonce"
    # Le thread principal n'a jamais posé de nonce : il reste à None.
    assert get_request_nonce() is None
