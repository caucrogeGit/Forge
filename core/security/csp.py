# pyright: strict
"""
core/security/csp.py — Nonce CSP par requête
=============================================
Mécanisme optionnel pour permettre des scripts inline contrôlés sans
ouvrir globalement la CSP avec unsafe-inline.

Utilisation :
    APP_CSP_NONCE_ENABLED=true dans env/dev ou env/prod.

    Dans un template Jinja :
        <script nonce="{{ csp_nonce() }}">/* script inline autorisé */</script>

Quand APP_CSP_NONCE_ENABLED=false (défaut), csp_nonce() retourne une
chaîne vide et la CSP ne contient pas de nonce — script-src 'self' seul.

Câblage par requête : poser le nonce via le gestionnaire de contexte
`request_nonce(...)`, qui garantit sa remise à zéro en fin de requête
(le stockage est thread-local et les threads sont réutilisés).
"""
import secrets
import threading
from collections.abc import Generator
from contextlib import contextmanager

_local = threading.local()

_CSP_BASE = "default-src 'self'; style-src 'self'; script-src 'self'{extra}; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'"


def generate_nonce() -> str:
    """Génère un nonce cryptographiquement sûr (URL-safe base64, 128 bits)."""
    return secrets.token_urlsafe(16)


def set_request_nonce(nonce: "str | None") -> None:
    """Stocke le nonce de la requête courante dans le stockage thread-local."""
    _local.nonce = nonce


def get_request_nonce() -> "str | None":
    """Retourne le nonce de la requête courante, ou None."""
    return getattr(_local, "nonce", None)


def clear_request_nonce() -> None:
    """Réinitialise le nonce de la requête courante."""
    _local.nonce = None


@contextmanager
def request_nonce(nonce: "str | None") -> "Generator[str | None, None, None]":
    """Porte le nonce CSP le temps d'une requête, puis garantit sa remise à zéro.

    Le stockage est thread-local et les threads sont réutilisés (serveur de
    dev) : sans remise à zéro en fin de requête, un nonce pourrait fuiter dans
    la CSP d'une requête suivante. Utiliser ce gestionnaire de contexte est la
    façon officielle de poser un nonce par requête, plutôt que d'appeler
    set_request_nonce directement.

        with request_nonce(generate_nonce()) as n:
            response.headers["Content-Security-Policy"] = build_csp_header(n)
            ...  # rendu du template, csp_nonce() retourne n
    """
    set_request_nonce(nonce)
    try:
        yield nonce
    finally:
        clear_request_nonce()


def build_csp_header(nonce: "str | None" = None) -> str:
    """
    Construit l'en-tête Content-Security-Policy.

    Avec nonce  → script-src 'self' 'nonce-<valeur>'
    Sans nonce  → script-src 'self'
    Jamais      → unsafe-inline
    """
    extra = f" 'nonce-{nonce}'" if nonce else ""
    return _CSP_BASE.format(extra=extra)
