from __future__ import annotations

from pathlib import PurePosixPath

# FILES-IMAGES-REPOINT-001 (ADR-019) : storage d'upload dans forge-mvc-files.
from forge_mvc_files.storage import normalize_media_path


_SELECT_COLUMNS = """
    Id AS id,
    EntityName AS entity_name,
    EntityId AS entity_id,
    Path AS path,
    OriginalName AS original_name,
    MimeType AS mime_type,
    Size AS size,
    Role AS role,
    Position AS position,
    AltText AS alt_text,
    CreatedAt AS created_at
"""


def create_media_record(
    *,
    entity_name: str,
    entity_id: int,
    path: str,
    original_name: str | None = None,
    mime_type: str | None = None,
    size: int | None = None,
    role: str = "default",
    position: int = 0,
    alt_text: str | None = None,
    db=None,
) -> int:
    entity_name = _validate_entity_name(entity_name)
    entity_id = _validate_positive_int("entity_id", entity_id)
    normalized_path = normalize_media_path(path)
    role = _validate_role(role)
    position = _validate_non_negative_int("position", position)
    stored_size = 0 if size is None else _validate_non_negative_int("size", size)
    stored_original_name = original_name or PurePosixPath(normalized_path).name
    stored_mime_type = mime_type or "application/octet-stream"

    sql = """
        INSERT INTO media
            (EntityName, EntityId, Path, OriginalName, MimeType, Size, Role, Position, AltText, CreatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    return _db(db).insert(
        sql,
        (
            entity_name,
            entity_id,
            normalized_path,
            stored_original_name,
            stored_mime_type,
            stored_size,
            role,
            position,
            alt_text,
        ),
    )


def attach_media_to_entity(
    saved_upload,
    *,
    entity_name: str,
    entity_id: int,
    role: str = "default",
    position: int | None = None,
    alt_text: str | None = None,
    db=None,
) -> int:
    _validate_saved_upload(saved_upload)
    return create_media_record(
        entity_name=entity_name,
        entity_id=entity_id,
        path=saved_upload.path,
        original_name=saved_upload.original_name,
        mime_type=saved_upload.mime_type,
        size=saved_upload.size,
        role=role,
        position=0 if position is None else position,
        alt_text=alt_text,
        db=db,
    )


def get_media_record(media_id: int, *, db=None) -> dict | None:
    media_id = _validate_positive_int("media_id", media_id)
    sql = f"""
        SELECT {_SELECT_COLUMNS}
        FROM media
        WHERE Id = ?
    """
    return _db(db).fetch_one(sql, (media_id,))


def list_media_for_entity(
    entity_name: str,
    entity_id: int,
    *,
    role: str | None = None,
    db=None,
) -> list[dict]:
    entity_name = _validate_entity_name(entity_name)
    entity_id = _validate_positive_int("entity_id", entity_id)

    clauses = ["EntityName = ?", "EntityId = ?"]
    params: list[object] = [entity_name, entity_id]
    if role is not None:
        clauses.append("Role = ?")
        params.append(_validate_role(role))

    sql = f"""
        SELECT {_SELECT_COLUMNS}
        FROM media
        WHERE {" AND ".join(clauses)}
        ORDER BY Position ASC, Id ASC
    """
    return _db(db).fetch_all(sql, tuple(params)) or []


def update_media_alt_text(media_id: int, alt_text: str | None, *, db=None) -> None:
    media_id = _validate_positive_int("media_id", media_id)
    if alt_text is not None:
        alt_text = alt_text.strip() or None
        if alt_text is not None and len(alt_text) > 255:
            raise ValueError("alt_text ne peut pas dépasser 255 caractères.")
    _db(db).execute(
        "UPDATE media SET AltText = ? WHERE Id = ?",
        (alt_text, media_id),
    )


def update_media_position(media_id: int, position: int, *, db=None) -> None:
    media_id = _validate_positive_int("media_id", media_id)
    position = _validate_non_negative_int("position", position)
    _db(db).execute(
        "UPDATE media SET Position = ? WHERE Id = ?",
        (position, media_id),
    )


def delete_media_record(media_id: int, *, db=None) -> bool:
    media_id = _validate_positive_int("media_id", media_id)
    rowcount = _db(db).execute("DELETE FROM media WHERE Id = ?", (media_id,))
    return rowcount > 0


def delete_media(
    media_id: int,
    *,
    delete_files: bool = False,
    variants: bool = True,
    db=None,
    root=None,
) -> dict:
    media_id = _validate_positive_int("media_id", media_id)
    media = get_media_record(media_id, db=db)
    if media is None:
        return {
            "deleted_record": False,
            "deleted_files": {},
        }

    deleted_files = {}
    if delete_files:
        from forge_mvc_files import delete_media_file

        deleted_files = delete_media_file(media["path"], root=root, variants=variants)

    return {
        "deleted_record": delete_media_record(media_id, db=db),
        "deleted_files": deleted_files,
    }


def _db(db):
    if db is not None:
        return db
    from core.database import db as database

    return database


def _validate_entity_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("entity_name est obligatoire.")
    return value.strip()


def _validate_role(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("role est obligatoire.")
    return value.strip()


def _validate_positive_int(name: str, value: int) -> int:
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} doit etre un entier positif.")
    return value


def _validate_non_negative_int(name: str, value: int) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} doit etre un entier positif ou nul.")
    return value


def _validate_saved_upload(value) -> None:
    required = ("path", "original_name", "mime_type", "size")
    if value is None or any(not hasattr(value, attr) for attr in required):
        raise TypeError("saved_upload doit ressembler a un SavedUpload.")
