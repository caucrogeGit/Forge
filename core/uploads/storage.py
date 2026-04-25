from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

from core.uploads.exceptions import UploadStorageError


_SAFE_CATEGORY = re.compile(r"^[A-Za-z0-9_-]+$")
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


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
