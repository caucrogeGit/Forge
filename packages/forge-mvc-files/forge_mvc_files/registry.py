# pyright: strict
"""Registre des fichiers écrits, socle des quotas et de la purge (ADR-094).

Ce module suit la convention des opt-ins sans état du paquet : il rend du SQL
et calcule des paramètres, l'appelant fournit l'exécuteur. `forge-mvc-files`
reste donc utilisable **sans base**, exactement comme avant, pour qui ne veut
que des primitives de stockage.

L'enregistrement est **explicite**. Écrire un fichier n'enregistre rien de soi
même : l'application appelle `record_file` quand elle le veut, comme elle
appelle déjà `save_upload`. Un opt-in qui écrirait en base à l'insu de son
appelant serait de la magie cachée, que le principe 3 refuse.

Le propriétaire est un couple libre, une nature et un identifiant. Le paquet ne
sait pas ce qu'est un utilisateur, et ne cherche pas à le savoir.
"""
from __future__ import annotations

from typing import Any, Protocol

from forge_mvc_files.tables import FILES_TABLE_NAME

__all__ = [
    "FileRegistryError",
    "DbLike",
    "record_file",
    "forget_file",
    "get_file_record",
    "owner_usage_bytes",
    "owner_file_count",
    "list_paths_for_owner",
    "list_all_paths",
]


class FileRegistryError(ValueError):
    """Entrée invalide pour le registre."""


class DbLike(Protocol):
    """Accès base minimal, fourni par l'appelant."""

    def execute(self, sql: str, params: "tuple[Any, ...] | list[Any]") -> int: ...

    def fetch_one(
        self, sql: str, params: "tuple[Any, ...] | list[Any]"
    ) -> "dict[str, Any] | None": ...

    def fetch_all(
        self, sql: str, params: "tuple[Any, ...] | list[Any]"
    ) -> "list[dict[str, Any]]": ...


_INSERT = (
    f"INSERT INTO {FILES_TABLE_NAME} "
    "(path, original_name, mime_type, size_bytes, owner_kind, owner_id) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
_DELETE = f"DELETE FROM {FILES_TABLE_NAME} WHERE path = ?"
_SELECT_ONE = (
    "SELECT path, original_name, mime_type, size_bytes, owner_kind, owner_id, created_at "
    f"FROM {FILES_TABLE_NAME} WHERE path = ?"
)
_SUM_FOR_OWNER = (
    f"SELECT COALESCE(SUM(size_bytes), 0) AS total FROM {FILES_TABLE_NAME} "
    "WHERE owner_kind = ? AND owner_id = ?"
)
_COUNT_FOR_OWNER = (
    f"SELECT COUNT(*) AS total FROM {FILES_TABLE_NAME} "
    "WHERE owner_kind = ? AND owner_id = ?"
)
_PATHS_FOR_OWNER = (
    f"SELECT path FROM {FILES_TABLE_NAME} "
    "WHERE owner_kind = ? AND owner_id = ? ORDER BY path"
)
_ALL_PATHS = f"SELECT path FROM {FILES_TABLE_NAME} ORDER BY path"


def _db(db: "DbLike | None") -> DbLike:
    if db is not None:
        return db
    from core.database import db as module

    return module  # pyright: ignore[reportReturnType]


def _owner(owner_kind: "str | None", owner_id: object) -> "tuple[str | None, str | None]":
    """Couple propriétaire normalisé, ou deux `None`.

    Les deux vont de pair : un identifiant sans nature ne désigne personne, et
    une nature sans identifiant non plus. Refuser tôt évite un quota qui compte
    des lignes qu'aucune requête ne retrouvera.
    """
    nature = (owner_kind or "").strip() or None
    identifiant = None if owner_id is None else str(owner_id).strip() or None
    if (nature is None) != (identifiant is None):
        raise FileRegistryError(
            "owner_kind et owner_id vont de pair : fournir les deux, ou aucun. "
            f"Reçu : owner_kind={owner_kind!r}, owner_id={owner_id!r}."
        )
    return nature, identifiant


def record_file(
    path: str,
    original_name: str,
    size_bytes: int,
    *,
    mime_type: "str | None" = None,
    owner_kind: "str | None" = None,
    owner_id: object = None,
    db: "DbLike | None" = None,
) -> None:
    """Inscrit un fichier écrit au registre.

    `path` est le chemin relatif rendu par `save_upload`, et sert de clé : la
    colonne est unique, deux lignes pour un même fichier rendant tout quota
    faux.

    Raises:
        FileRegistryError: chemin ou nom vide, taille négative, ou couple
            propriétaire incomplet.
    """
    chemin = (path or "").strip()
    if not chemin:
        raise FileRegistryError("path ne peut pas être vide.")
    nom = (original_name or "").strip()
    if not nom:
        raise FileRegistryError("original_name ne peut pas être vide.")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise FileRegistryError(f"size_bytes doit être un entier. Reçu : {size_bytes!r}.")
    if size_bytes < 0:
        raise FileRegistryError(f"size_bytes ne peut pas être négatif. Reçu : {size_bytes}.")

    nature, identifiant = _owner(owner_kind, owner_id)
    _db(db).execute(
        _INSERT, (chemin, nom, (mime_type or None), size_bytes, nature, identifiant)
    )


def forget_file(path: str, *, db: "DbLike | None" = None) -> bool:
    """Retire un fichier du registre. Vrai s'il y était.

    Ne supprime aucun fichier sur disque : l'appelant décide de l'ordre, et le
    registre ne touche jamais au système de fichiers.
    """
    chemin = (path or "").strip()
    if not chemin:
        return False
    return _db(db).execute(_DELETE, (chemin,)) >= 1


def get_file_record(path: str, *, db: "DbLike | None" = None) -> "dict[str, Any] | None":
    """Ligne du registre pour `path`, ou `None`.

    Sert notamment à retrouver le nom d'origine, que le mode UUID efface du
    chemin par sécurité.
    """
    chemin = (path or "").strip()
    if not chemin:
        return None
    return _db(db).fetch_one(_SELECT_ONE, (chemin,))


def owner_usage_bytes(owner_kind: str, owner_id: object, *, db: "DbLike | None" = None) -> int:
    """Somme des tailles inscrites pour un propriétaire. Socle d'un quota."""
    nature, identifiant = _owner(owner_kind, owner_id)
    if nature is None:
        return 0
    ligne = _db(db).fetch_one(_SUM_FOR_OWNER, (nature, identifiant))
    return int(ligne["total"]) if ligne and ligne.get("total") is not None else 0


def owner_file_count(owner_kind: str, owner_id: object, *, db: "DbLike | None" = None) -> int:
    """Nombre de fichiers inscrits pour un propriétaire."""
    nature, identifiant = _owner(owner_kind, owner_id)
    if nature is None:
        return 0
    ligne = _db(db).fetch_one(_COUNT_FOR_OWNER, (nature, identifiant))
    return int(ligne["total"]) if ligne else 0


def list_paths_for_owner(
    owner_kind: str, owner_id: object, *, db: "DbLike | None" = None
) -> list[str]:
    """Chemins inscrits pour un propriétaire, triés."""
    nature, identifiant = _owner(owner_kind, owner_id)
    if nature is None:
        return []
    return [str(r["path"]) for r in _db(db).fetch_all(_PATHS_FOR_OWNER, (nature, identifiant))]


def list_all_paths(*, db: "DbLike | None" = None) -> list[str]:
    """Tous les chemins inscrits, triés.

    Sert à rapprocher le registre du disque pour repérer les orphelins. Le
    rapprochement lui même appartient à l'appelant, qui seul connaît sa racine.
    """
    return [str(r["path"]) for r in _db(db).fetch_all(_ALL_PATHS, ())]
