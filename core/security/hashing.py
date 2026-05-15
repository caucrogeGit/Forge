"""
core/security/hashing.py — Vérification PBKDF2 (module legacy, lecture seule)
==============================================================================
Ce module ne crée plus de nouveaux hashes depuis Forge 2.10.0
(ticket HASHING-PBKDF2-REMOVE-001).

Il sert uniquement à vérifier les hashes PBKDF2-HMAC-SHA256 existants en base,
créés par des versions antérieures de Forge.

Pour créer de nouveaux hashes, utiliser `core.auth.password.hash_password`
(Argon2id, API officielle).

À chaque connexion réussie avec un hash PBKDF2, le hash est automatiquement
migré vers Argon2id (mécanisme AUTH-HASH-MIGRATION-001, transparent).

Quand tous les hashes PBKDF2 auront migré, ce module sera entièrement
supprimé (ticket HASHING-PBKDF2-DEFINITIVE-REMOVE-001, post-3.0).

Responsabilités restantes :

1. Vérification PBKDF2 legacy (lecture seule)
   - verify_password_legacy() : vérifie un mot de passe contre un hash stocké
   - pbkdf2_needs_rehash() : indique qu'un hash doit migrer vers Argon2id

   Formats vérifiables :
       "pbkdf2_sha256$<iterations>$<sel_hex>$<hash_hex>"  (format versionné)
       "<sel_hex>:<hash_hex>"  (itérations = LEGACY_ITERATIONS, format legacy)

2. Limitation du débit sur /login (rate limiting)
   - record_attempt() : note l'heure de la tentative pour une IP
   - is_rate_limited() : retourne True si l'IP a dépassé la limite autorisée

   Fenêtre glissante : MAX_ATTEMPTS tentatives par RATE_LIMIT_WINDOW.
   Stockage en mémoire — remis à zéro au redémarrage du serveur.
"""
import hashlib
import hmac

# ── Vérification PBKDF2 legacy ────────────────────────────────────────────────

LEGACY_ITERATIONS = 260_000  # itérations des hashes créés avant Forge 2.x
_PREFIX = "pbkdf2_sha256$"

# Note : ITERATIONS (600 000, création) supprimé — hacher_mot_de_passe retirée.
# Utiliser core.auth.password.hash_password() (Argon2id) pour les nouveaux hashes.


def verify_password_legacy(password: str, stored_hash: str) -> bool:
    """
    Vérifie un mot de passe contre un hash PBKDF2 stocké (legacy).

    Supporte deux formats :
    - Versionné : "pbkdf2_sha256$<iterations>$<sel_hex>$<hash_hex>"
    - Legacy    : "<sel_hex>:<hash_hex>" (itérations = LEGACY_ITERATIONS)

    Note : le suffixe _legacy distingue cette fonction de
    core.auth.password.verify_password (Argon2id, API officielle).
    """
    try:
        if stored_hash.startswith(_PREFIX):
            _, iterations_str, sel_hex, hash_hex = stored_hash.split("$", 3)
            iterations = int(iterations_str)
        else:
            sel_hex, hash_hex = stored_hash.split(":", 1)
            iterations = LEGACY_ITERATIONS
        sel     = bytes.fromhex(sel_hex)
        attendu = bytes.fromhex(hash_hex)
        calcule = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, iterations)
        return hmac.compare_digest(calcule, attendu)
    except (ValueError, TypeError):
        return False


def pbkdf2_needs_rehash(stored_hash: str) -> bool:
    """Retourne True pour tout hash PBKDF2 — tous doivent migrer vers Argon2id.

    Utilisé par le mécanisme de migration au login (AUTH-HASH-MIGRATION-001).
    Depuis Forge 2.10.0, tout hash PBKDF2 (quel que soit son coût) doit être
    rehaché en Argon2id à la prochaine connexion réussie.
    """
    return True


# ── Rate limiting — délégué à core.auth.rate_limit (HASHING-RATELIMIT-MOVE-001) ─
# Les fonctions et constantes suivantes sont re-exportées pour la compatibilité
# avec les imports existants (auth_controller, tests, starters).

from core.auth.rate_limit import (  # noqa: E402
    record_login_attempt as record_attempt,       # noqa: F401
    is_login_rate_limited as is_rate_limited,     # noqa: F401
    LOGIN_MAX_ATTEMPTS as MAX_ATTEMPTS,           # noqa: F401
    LOGIN_RATE_LIMIT_WINDOW as RATE_LIMIT_WINDOW, # noqa: F401
)
