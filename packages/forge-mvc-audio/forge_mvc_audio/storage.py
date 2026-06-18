# pyright: strict
"""Disposition des fichiers audio sur disque — sans état.

Le stockage est **uuid-based** : le nom de fichier fourni par l'utilisateur
n'apparaît **jamais** dans le chemin (anti-traversal par construction). Seule
l'extension, validée contre une liste blanche, est conservée.

Disposition (sous ``FORGE_AUDIO_STORAGE_ROOT``), **non partitionnée par date**
pour permettre le lookup par ``uuid`` seul (pas de base de données) :

    originals/<uuid>/source<ext>
    transcoded/<uuid>/audio.mp3

Le lookup de lecture (``resolve_playable_relpath``) cherche d'abord le MP3
transcodé, puis la source — uniquement à l'intérieur du dossier de l'``uuid``.
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

__all__ = [
    "ALLOWED_EXTENSIONS",
    "safe_extension",
    "is_valid_uuid",
    "original_relpath",
    "transcoded_relpath",
    "store_original",
    "resolve_playable_relpath",
]

# Conteneurs/formats audio acceptés en entrée. La sortie de transcodage est MP3.
ALLOWED_EXTENSIONS = frozenset({".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"})


def safe_extension(filename: str) -> str:
    """Extension en minuscules du nom fourni (``""`` si aucune)."""
    return Path(filename or "").suffix.lower()


def is_valid_uuid(value: str) -> bool:
    """Vrai si ``value`` est un UUID canonique (clé de lookup sûre)."""
    try:
        return str(UUID(str(value))) == str(value).lower()
    except (ValueError, AttributeError, TypeError):
        return False


def original_relpath(uuid: str, ext: str) -> str:
    """Chemin relatif de la source, uuid-based."""
    return f"originals/{uuid}/source{ext}"


def transcoded_relpath(uuid: str) -> str:
    """Chemin relatif du MP3 transcodé, uuid-based."""
    return f"transcoded/{uuid}/audio.mp3"


def store_original(
    data: bytes, uuid: str, ext: str, *, storage_root: str
) -> str:
    """Écrit la source à un emplacement uuid-based ; retourne le chemin relatif.

    L'``uuid`` est validé avant toute construction de chemin : il apparaît dans
    l'arborescence (``originals/<uuid>/``), donc un uuid non canonique fourni par
    l'appelant serait un vecteur de traversal à l'écriture. La symétrie avec
    ``resolve_playable_relpath`` (qui valide en lecture) est ainsi garantie.
    """
    if not is_valid_uuid(uuid):
        raise ValueError(f"uuid audio invalide (anti-traversal) : {uuid!r}")
    rel = original_relpath(uuid, ext)
    target = Path(storage_root) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return rel


def resolve_playable_relpath(uuid: str, *, storage_root: str) -> str | None:
    """Retrouve le fichier lisible pour ``uuid`` (sans base de données).

    Préfère le MP3 transcodé s'il existe, sinon la source d'origine. Retourne le
    chemin **relatif** (sous ``storage_root``) ou ``None`` si rien n'est trouvé.
    Refuse tout ``uuid`` qui n'est pas un UUID canonique (anti-traversal).
    """
    if not is_valid_uuid(uuid):
        return None
    root = Path(storage_root)

    transcoded = transcoded_relpath(uuid)
    if (root / transcoded).is_file():
        return transcoded

    source_dir = root / "originals" / uuid
    if source_dir.is_dir():
        for entry in sorted(source_dir.glob("source.*")):
            if entry.is_file():
                return f"originals/{uuid}/{entry.name}"
    return None
