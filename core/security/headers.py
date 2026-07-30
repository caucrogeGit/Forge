# pyright: strict
"""core/security/headers.py — Helper centralisé des headers HTTP de sécurité.

Ticket : WSGI-SECURITY-HEADERS-001.

Forge applique le même socle de headers de sécurité navigateur sur les deux
chemins de sortie HTTP :

  * `python app.py` — serveur de développement (RequestHandler dans `app.py`)
  * WSGI — adaptateur `core.app.wsgi._response_to_wsgi`

Le helper `apply_security_headers(headers, ...)` mute le dict de headers en
posant les valeurs par défaut via ``setdefault`` — il n'écrase jamais un
header explicitement défini par l'application. C'est la seule source de
vérité du contrat de sécurité Forge.

Décision HSTS
-------------
`Strict-Transport-Security` n'est pertinent que sur HTTPS et peut bloquer
l'accès si émis à tort. Le helper expose `include_hsts: bool` :

  * ``app.py`` passe ``True`` inconditionnellement — c'est un serveur de dev
    qui sait s'il sert TLS (la branche TLS est gardée par ``APP_SSL_ENABLED``).
  * Le chemin WSGI passe ``True`` uniquement si ``environ["wsgi.url_scheme"]
    == "https"`` (la requête a réellement atteint Forge en TLS). Derrière un
    reverse proxy qui termine TLS, ``wsgi.url_scheme`` vaut ``http`` côté
    Forge — c'est alors le reverse proxy qui doit poser HSTS, et c'est sa
    bonne pratique documentée (`docs/deployment/wsgi-deployment.md`).

Voir `tests/test_wsgi_security_headers_001.py` pour le verrouillage de ces
invariants.
"""
from __future__ import annotations


_DEFAULT_HEADERS: tuple[tuple[str, str], ...] = (
    ("X-Frame-Options", "DENY"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"),
)

_HSTS_NAME = "Strict-Transport-Security"
_HSTS_VALUE = "max-age=31536000; includeSubDomains"

_CSP_NAME = "Content-Security-Policy"


def apply_security_headers(
    headers: dict[str, str],
    *,
    include_hsts: bool,
    csp: str | None = None,
) -> None:
    """Pose les headers de sécurité Forge par défaut sur ``headers``.

    Mute le dict en place via ``setdefault`` — un header explicitement défini
    par l'application n'est jamais écrasé.

    Args:
        headers: dict de headers HTTP à enrichir. Les clés et valeurs doivent
            être des ``str``.
        include_hsts: si ``True``, pose ``Strict-Transport-Security`` (avec la
            même valeur que ``app.py`` historiquement). Voir le module
            docstring pour la décision HSTS par chemin.
        csp: valeur Content-Security-Policy à poser si l'application n'en a
            pas défini une. Si ``None``, la CSP n'est pas ajoutée — utile pour
            les chemins qui ne peuvent pas la calculer (ex. avant d'avoir un
            nonce de requête).
    """
    for name, value in _DEFAULT_HEADERS:
        headers.setdefault(name, value)
    if include_hsts:
        headers.setdefault(_HSTS_NAME, _HSTS_VALUE)
    if csp is not None:
        headers.setdefault(_CSP_NAME, csp)


# ── Neutralisation de l'injection d'en-têtes (CORE-HEADER-CRLF-001) ──────────

class HeaderInjectionError(ValueError):
    """Une valeur d'en-tête porte un saut de ligne : la réponse est refusée.

    Un `CR` ou un `LF` dans une valeur d'en-tête termine la ligne pour le
    client, qui lit la suite comme un **nouvel en-tête**, voire comme le début
    du corps. Une donnée utilisateur reprise dans un en-tête, un nom de fichier
    en `Content-Disposition` ou une cible de redirection en `Location`, laisse
    alors poser n'importe quel en-tête et découper la réponse.

    Mesuré avant correctif sur les deux chemins de sortie de Forge : les quatre
    charges d'essai, `CRLF`, `LF` seul, `CR` seul et fin d'en-têtes suivie d'un
    corps, sortaient avec leur saut intact.

    Forge **refuse** la réponse plutôt que de retirer le caractère en silence.
    Retirer modifierait une donnée applicative sans le dire, et la norme HTTP
    n'admet aucun saut de ligne dans une valeur : il n'y a donc pas de cas
    légitime à préserver. C'est aussi ce que font les autres cadres Python.
    """


def assert_headers_are_safe(headers: "dict[str, str]") -> None:
    """Refuse tout en-tête dont le nom ou la valeur porte un saut de ligne.

    À appeler **avant** d'émettre quoi que ce soit : une fois la première ligne
    envoyée, il est trop tard pour changer d'avis, et le serveur de dév émet
    ses en-têtes un par un.

    Le nom est contrôlé au même titre que la valeur : une clé forgée y ferait
    passer la même chose.
    """
    for nom, valeur in headers.items():
        for texte, quoi in ((str(nom), "nom"), (str(valeur), "valeur")):
            if "\r" in texte or "\n" in texte:
                raise HeaderInjectionError(
                    f"En-tête refusé : le {quoi} contient un saut de ligne "
                    f"(injection d'en-têtes). En-tête : {str(nom)[:40]!r}."
                )
