import hashlib
import os


from core.security.hashing import (
    LEGACY_ITERATIONS,
    MAX_ATTEMPTS,
    record_attempt,
    is_rate_limited,
    pbkdf2_needs_rehash,
    verify_password_legacy,
)

IP = "192.168.1.100"


# ── Helpers de test ───────────────────────────────────────────────────────────

def _create_pbkdf2_versioned_hash(password: str, iterations: int = 600_000) -> str:
    """Crée un hash PBKDF2 au format versionné sans utiliser l'API supprimée."""
    sel = os.urandom(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, iterations)
    return f"pbkdf2_sha256${iterations}${sel.hex()}${hash_.hex()}"


# ── Constantes ────────────────────────────────────────────────────────────────

class TestConstantes:

    def test_legacy_iterations_egale_260000(self):
        assert LEGACY_ITERATIONS == 260_000


# ── Vérification des hashes PBKDF2 ───────────────────────────────────────────

class TestVerification:

    def test_verification_hash_versionne_correct(self):
        h = _create_pbkdf2_versioned_hash("monmdp")
        assert verify_password_legacy("monmdp", h) is True

    def test_verification_hash_versionne_incorrect(self):
        h = _create_pbkdf2_versioned_hash("monmdp")
        assert verify_password_legacy("mauvais", h) is False

    def test_deux_hashes_du_meme_mdp_sont_differents(self):
        h1 = _create_pbkdf2_versioned_hash("monmdp")
        h2 = _create_pbkdf2_versioned_hash("monmdp")
        assert h1 != h2  # sels aléatoires différents


# ── Compatibilité ancien format legacy ────────────────────────────────────────

class TestCompatibiliteLegacy:

    def _make_legacy_hash(self, password: str) -> str:
        """Génère un hash au format <sel_hex>:<hash_hex> avec LEGACY_ITERATIONS."""
        sel = os.urandom(16)
        hash_ = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, LEGACY_ITERATIONS)
        return sel.hex() + ":" + hash_.hex()

    def test_ancien_format_reste_verifiable(self):
        h = self._make_legacy_hash("monmdp")
        assert verify_password_legacy("monmdp", h) is True

    def test_ancien_format_mauvais_mdp_echoue(self):
        h = self._make_legacy_hash("monmdp")
        assert verify_password_legacy("mauvais", h) is False

    def test_ancien_format_ne_passe_pas_avec_nouveau_iterations(self):
        """Un hash legacy créé avec 260k itérations échoue si on lui applique 600k."""
        sel = os.urandom(16)
        hash_ = hashlib.pbkdf2_hmac("sha256", "monmdp".encode(), sel, LEGACY_ITERATIONS)
        hash_legacy = sel.hex() + ":" + hash_.hex()
        # verify_password_legacy doit utiliser LEGACY_ITERATIONS, pas 600k
        assert verify_password_legacy("monmdp", hash_legacy) is True

    def test_format_invalide_retourne_false(self):
        assert verify_password_legacy("monmdp", "pas_de_double_point") is False

    def test_hash_vide_retourne_false(self):
        assert verify_password_legacy("monmdp", "") is False

    def test_argon2id_format_retourne_false(self):
        """verify_password_legacy ne reconnaît pas un hash Argon2id."""
        assert verify_password_legacy("monmdp", "$argon2id$v=19$m=65536,t=2,p=1$fake") is False


# ── pbkdf2_needs_rehash ────────────────────────────────────────────────────────

class TestPbkdf2NeedsRehash:

    def test_format_legacy_needs_rehash(self):
        sel = os.urandom(16)
        hash_ = hashlib.pbkdf2_hmac("sha256", "x".encode(), sel, LEGACY_ITERATIONS)
        h = sel.hex() + ":" + hash_.hex()
        assert pbkdf2_needs_rehash(h) is True

    def test_hash_versionne_needs_rehash(self):
        """Depuis 2.10.0, tout hash PBKDF2 doit migrer vers Argon2id."""
        h = _create_pbkdf2_versioned_hash("monmdp")
        assert pbkdf2_needs_rehash(h) is True

    def test_hash_sous_dimensionne_needs_rehash(self):
        sel = os.urandom(16)
        hash_ = hashlib.pbkdf2_hmac("sha256", "x".encode(), sel, 260_000)
        h = f"pbkdf2_sha256$260000${sel.hex()}${hash_.hex()}"
        assert pbkdf2_needs_rehash(h) is True

    def test_hash_invalide_needs_rehash(self):
        assert pbkdf2_needs_rehash("") is True
        assert pbkdf2_needs_rehash("garbage") is True

    def test_argon2id_hash_needs_rehash(self):
        """pbkdf2_needs_rehash retourne True pour un hash Argon2id (n'est pas PBKDF2)."""
        assert pbkdf2_needs_rehash("$argon2id$v=19$m=65536,t=2,p=1$fake$hash") is True


# ── Rate limiting ──────────────────────────────────────────────────────────────

class TestRateLimiting:

    def test_pas_limite_initialement(self):
        assert is_rate_limited(IP) is False

    def test_sous_la_limite(self):
        for _ in range(MAX_ATTEMPTS - 1):
            record_attempt(IP)
        assert is_rate_limited(IP) is False

    def test_limite_atteinte(self):
        for _ in range(MAX_ATTEMPTS):
            record_attempt(IP)
        assert is_rate_limited(IP) is True

    def test_ips_independantes(self):
        for _ in range(MAX_ATTEMPTS):
            record_attempt(IP)
        assert is_rate_limited("10.0.0.1") is False
