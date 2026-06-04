"""Shim transitoire — rate-limit d'upload déplacé vers forge-mvc-files.

FILES-MOVE-PIPELINE-001 (ADR-019) : le rate-limit d'upload vit désormais dans
``forge_mvc_files.rate_limit``. Ce module réexporte pour ne pas casser les
imports ``from core.uploads.rate_limit import ...`` pendant la migration ; il
sera supprimé avec ``core/uploads/`` au ticket ``CORE-DROP-UPLOADS-001``.

⚠️ Pour **monkeypatcher** les constantes (``UPLOAD_MAX_PAR_FENETRE``,
``UPLOAD_RATE_LIMIT_WINDOW``) et que les fonctions en tiennent compte, importer
le **vrai** module : ``import forge_mvc_files.rate_limit``. Nouveau code :
importer depuis ``forge_mvc_files``.
"""

from forge_mvc_files.rate_limit import (
    UPLOAD_MAX_PAR_FENETRE,
    UPLOAD_RATE_LIMIT_WINDOW,
    is_upload_rate_limited,
    record_upload_attempt,
)

__all__ = [
    "UPLOAD_MAX_PAR_FENETRE",
    "UPLOAD_RATE_LIMIT_WINDOW",
    "is_upload_rate_limited",
    "record_upload_attempt",
]
