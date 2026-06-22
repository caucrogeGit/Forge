"""Chargement explicite de la configuration du projet Forge courant."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


class ProjectConfigError(ValueError):
    """Erreur de chargement du config.py du projet courant."""


def load_project_config(root: Path | None = None) -> ModuleType:
    """Charge root/config.py sans dépendre du package installé par pipx."""
    project_root = (root or Path.cwd()).resolve()
    config_path = project_root / "config.py"
    if not config_path.exists():
        raise ProjectConfigError(
            f"Projet Forge introuvable : config.py absent dans {project_root.as_posix()}."
        )

    module_key = "_forge_project_config"
    root_str = str(project_root)
    old_cwd = Path.cwd()
    path_added = root_str not in sys.path

    if path_added:
        sys.path.insert(0, root_str)
    sys.modules.pop(module_key, None)

    try:
        os.chdir(project_root)
        spec = importlib.util.spec_from_file_location(module_key, config_path)
        if spec is None or spec.loader is None:
            raise ProjectConfigError(f"Chargement impossible : {config_path.as_posix()}.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except ProjectConfigError:
        raise
    except Exception as exc:
        raise ProjectConfigError(f"Configuration projet invalide : {exc}") from exc
    finally:
        os.chdir(old_cwd)
        if path_added:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass
        sys.modules.pop(module_key, None)
