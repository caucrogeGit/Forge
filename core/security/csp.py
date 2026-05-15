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
"""
import secrets
import threading

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


def build_csp_header(nonce: "str | None" = None) -> str:
    """
    Construit l'en-tête Content-Security-Policy.

    Avec nonce  → script-src 'self' 'nonce-<valeur>'
    Sans nonce  → script-src 'self'
    Jamais      → unsafe-inline
    """
    extra = f" 'nonce-{nonce}'" if nonce else ""
    return _CSP_BASE.format(extra=extra)
