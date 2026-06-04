"""Forge MVC Files — module opt-in propriétaire de l'upload générique.

Ce paquet récupère le **pipeline d'upload générique** extrait du core
(ADR-019) : écriture disque sécurisée (anti-traversal), service de fichiers
(`serve_media_file`, Range), suppression, rate-limit d'upload, et l'API
``save_upload`` / ``SavedUpload``.

À ce stade (``FILES-PKG-SCAFFOLD-001``), le paquet est un **squelette** : aucune
logique n'a encore été déplacée. Le core conserve l'upload jusqu'aux tickets de
déplacement (``FILES-MOVE-PIPELINE-001``). Les **validators purs** et la
hiérarchie ``UploadError`` resteront, eux, dans le core (utilisés par
``core/forms``, qui ne peut pas dépendre d'un opt-in — ADR-004). Voir
``docs/adr/019-upload-extraction.md``.
"""

from __future__ import annotations

__version__ = "1.0.0b13"

__all__: list[str] = []
