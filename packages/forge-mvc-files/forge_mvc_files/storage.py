from __future__ import annotations

import os
import posixpath
import re
from pathlib import Path
from uuid import uuid4

# FILES-MOVE-PIPELINE-001 (ADR-019) : validation/exceptions restent dans le core.
from core.forms.upload_exceptions import UploadStorageError


_SAFE_CATEGORY = re.compile(r"^[A-Za-z0-9_-]+$")
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def ensure_upload_dirs(root: str | Path, categories=("images", "documents", "tmp")) -> list[Path]:
    root_path = Path(root)
    created: list[Path] = []
    root_path.mkdir(parents=True, exist_ok=True)
    created.append(root_path)
    for category in categories:
        directory = root_path / safe_category(category)
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created


def safe_category(category: str) -> str:
    category = (category or "").strip()
    if not category or not _SAFE_CATEGORY.fullmatch(category):
        raise UploadStorageError(f"Categorie d'upload invalide : {category!r}.")
    return category


def secure_filename(filename: str) -> str:
    base = os.path.basename(filename or "").strip().replace(" ", "_")
    base = _UNSAFE_CHARS.sub("_", base).strip("._")
    if not base:
        raise UploadStorageError("Nom de fichier vide apres normalisation.")
    return base


def generate_unique_filename(original_name: str) -> str:
    safe_name = secure_filename(original_name)
    path = Path(safe_name)
    stem = path.stem or "upload"
    suffix = path.suffix.lower()
    return f"{stem}-{uuid4().hex}{suffix}"


def normalize_media_path(path: str) -> str:
    """Retourne un chemin media relatif, normalise et sur.

    Le chemin retourne est destine a etre stocke en base, typiquement dans
    `Media.path`. Il est toujours relatif a `storage/uploads`.
    """
    if not isinstance(path, str):
        raise UploadStorageError("Chemin media invalide.")

    value = path.strip()
    if not value:
        raise UploadStorageError("Chemin media vide.")
    if "\x00" in value:
        raise UploadStorageError("Chemin media invalide.")
    if _URI_SCHEME.match(value):
        raise UploadStorageError("Chemin media absolu ou URL interdit.")

    value = value.replace("\\", "/")
    while "//" in value:
        value = value.replace("//", "/")
    if value.startswith("/"):
        raise UploadStorageError("Chemin media absolu interdit.")

    normalized = posixpath.normpath(value)
    if normalized in {"", "."}:
        raise UploadStorageError("Chemin media vide.")
    if normalized == "storage/uploads":
        raise UploadStorageError("Chemin media incomplet.")
    if normalized.startswith("storage/uploads/"):
        normalized = normalized[len("storage/uploads/"):]

    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise UploadStorageError("Chemin media avec traversal interdit.")
    if normalized.startswith("../") or normalized == "..":
        raise UploadStorageError("Chemin media avec traversal interdit.")
    return normalized


def is_safe_media_path(path: str) -> bool:
    try:
        normalize_media_path(path)
    except UploadStorageError:
        return False
    return True


def media_path_to_storage_path(path: str, *, root: str | Path) -> Path:
    root_path = Path(root).resolve()
    relative_path = normalize_media_path(path)
    target = (root_path / relative_path).resolve()
    try:
        if os.path.commonpath([root_path, target]) != str(root_path):
            raise UploadStorageError("Chemin media hors du dossier d'upload.")
    except ValueError as exc:
        raise UploadStorageError("Chemin media invalide.") from exc
    return target


def category_dir(root: str | Path, category: str) -> Path:
    root_path = Path(root).resolve()
    directory = (root_path / safe_category(category)).resolve()
    try:
        if os.path.commonpath([root_path, directory]) != str(root_path):
            raise UploadStorageError("Chemin d'upload hors du dossier racine.")
    except ValueError as exc:
        raise UploadStorageError("Chemin d'upload invalide.") from exc
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_upload_path(filename: str, category: str, *, root: str | Path) -> Path:
    filename = secure_filename(filename)
    target = (category_dir(root, category) / filename).resolve()
    root_path = Path(root).resolve()
    try:
        if os.path.commonpath([root_path, target]) != str(root_path):
            raise UploadStorageError("Chemin d'upload hors du dossier racine.")
    except ValueError as exc:
        raise UploadStorageError("Chemin d'upload invalide.") from exc
    return target


def save_bytes(data: bytes, *, original_name: str, category: str, root: str | Path) -> Path:
    directory = category_dir(root, category)
    for _ in range(20):
        filename = generate_unique_filename(original_name)
        target = directory / filename
        try:
            with target.open("xb") as file:
                file.write(data)
            return target
        except FileExistsError:
            continue
        except OSError as exc:
            raise UploadStorageError(f"Impossible d'enregistrer le fichier : {exc}") from exc
    raise UploadStorageError("Impossible de generer un nom de fichier unique.")


def delete_file(path: str | Path, *, root: str | Path) -> bool:
    root_path = Path(root).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = root_path / target
    target = target.resolve()
    try:
        if os.path.commonpath([root_path, target]) != str(root_path):
            raise UploadStorageError("Suppression refusee hors du dossier d'upload.")
    except ValueError as exc:
        raise UploadStorageError("Chemin d'upload invalide.") from exc
    if not target.exists():
        return False
    if not target.is_file():
        raise UploadStorageError("Suppression refusee : le chemin n'est pas un fichier.")
    try:
        target.unlink()
        return True
    except OSError as exc:
        raise UploadStorageError(f"Impossible de supprimer le fichier : {exc}") from exc
