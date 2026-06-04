"""Rate limiting pour les routes d'upload (mémoire, fenêtre glissante).

Même structure que core.security.hashing pour le login : dict en mémoire,
thread-safe, fenêtre glissante. Les compteurs upload sont isolés des
compteurs de connexion.

Usage dans un contrôleur :

    from forge_mvc_files.rate_limit import is_upload_rate_limited, record_upload_attempt

    def upload_avatar(request):
        if is_upload_rate_limited(request.ip):
            body = json.dumps({
                "success": False,
                "error": {"code": "rate_limited", "message": "Trop d'uploads."},
            }).encode()
            return Response(429, body, "application/json")
        record_upload_attempt(request.ip)
        # ... traitement normal
"""
from __future__ import annotations

import threading
import time

UPLOAD_MAX_PAR_FENETRE: int = 10      # uploads autorisés par fenêtre par IP
UPLOAD_RATE_LIMIT_WINDOW: int = 60    # durée de la fenêtre glissante (secondes)

_compteurs: dict[str, list[float]] = {}
_lock = threading.Lock()


def is_upload_rate_limited(ip: str) -> bool:
    """Retourne True si l'IP a atteint la limite d'uploads sur la fenêtre courante."""
    with _lock:
        maintenant = time.time()
        historique = _compteurs.get(ip, [])
        recents = [t for t in historique if maintenant - t < UPLOAD_RATE_LIMIT_WINDOW]
        if recents:
            _compteurs[ip] = recents
        else:
            _compteurs.pop(ip, None)
        return len(recents) >= UPLOAD_MAX_PAR_FENETRE


def record_upload_attempt(ip: str) -> None:
    """Enregistre une tentative d'upload pour cette IP."""
    with _lock:
        maintenant = time.time()
        historique = _compteurs.get(ip, [])
        historique.append(maintenant)
        recents = [t for t in historique if maintenant - t < UPLOAD_RATE_LIMIT_WINDOW]
        _compteurs[ip] = recents
