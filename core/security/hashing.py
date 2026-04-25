"""
core/security.py — Utilitaires de sécurité
===========================================
Deux responsabilités :

1. Hachage du mot de passe (PBKDF2-HMAC-SHA256)
   - hacher_mot_de_passe() : génère un hash à partir d'un mot de passe en clair
   - verifier_mot_de_passe() : compare un mot de passe saisi avec le hash stocké

   Format stocké : "<sel_hex>:<hash_hex>"
   Le sel (16 octets aléatoires) est unique par mot de passe et empêche les
   attaques par table arc-en-ciel. PBKDF2 avec 260 000 itérations ralentit
   les attaques par force brute.

2. Limitation du débit sur /login (rate limiting)
   - enregistrer_tentative() : note l'heure de la tentative pour une IP
   - est_limite() : retourne True si l'IP a dépassé la limite autorisée

   Fenêtre glissante : MAX_TENTATIVES tentatives par FENETRE_SECONDES.
   Stockage en mémoire — remis à zéro au redémarrage du serveur.
"""
import hashlib
import hmac
import os
import threading
import time

# ── Hachage ────────────────────────────────────────────────────────────────────

ITERATIONS = 260_000  # OWASP 2023 : minimum 210 000 pour PBKDF2-SHA256


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Retourne '<sel_hex>:<hash_hex>' prêt à être stocké dans .env."""
    sel   = os.urandom(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, ITERATIONS)
    return sel.hex() + ":" + hash_.hex()


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """
    Compare le mot de passe saisi avec le hash stocké.
    Utilise hmac.compare_digest via hashlib pour éviter les timing attacks.
    """
    try:
        sel_hex, hash_hex = hash_stocke.split(":", 1)
        sel    = bytes.fromhex(sel_hex)
        attendu = bytes.fromhex(hash_hex)
        calcule = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, ITERATIONS)
        return hmac.compare_digest(calcule, attendu)
    except (ValueError, TypeError):
        return False


# ── Rate limiting ──────────────────────────────────────────────────────────────

MAX_TENTATIVES   = 5    # tentatives autorisées par fenêtre
FENETRE_SECONDES = 60   # durée de la fenêtre glissante (secondes)

_tentatives: dict[str, list[float]] = {}
_lock_tentatives = threading.Lock()


def enregistrer_tentative(ip: str) -> None:
    """Ajoute un horodatage pour cette IP."""
    with _lock_tentatives:
        maintenant = time.time()
        historique = _tentatives.get(ip, [])
        historique.append(maintenant)
        recentes = [t for t in historique if maintenant - t < FENETRE_SECONDES]
        if recentes:
            _tentatives[ip] = recentes
        else:
            _tentatives.pop(ip, None)


def est_limite(ip: str) -> bool:
    """Retourne True si l'IP a atteint la limite de tentatives."""
    with _lock_tentatives:
        maintenant = time.time()
        historique = _tentatives.get(ip, [])
        recentes   = [t for t in historique if maintenant - t < FENETRE_SECONDES]
        if recentes:
            _tentatives[ip] = recentes
        else:
            _tentatives.pop(ip, None)
        return len(recentes) >= MAX_TENTATIVES
