"""Garde-fou FILES-MOVE-PIPELINE-001 (ADR-019).

Le pipeline d'I/O d'upload (``manager`` + ``storage`` + ``rate_limit``) a quitté
le core pour ``forge-mvc-files`` :

- le vrai code vit dans ``forge_mvc_files/{manager,storage,rate_limit}.py`` ;
- ``forge_mvc_files`` expose l'API publique (``save_upload``, ``serve_media_file``,
  ``SavedUpload``, storage, rate-limit) ;
- ``core/uploads/{manager,storage,rate_limit}.py`` ne sont plus que des **shims**
  réexportant ``forge_mvc_files`` (supprimés au ticket ``CORE-DROP-UPLOADS-001``) ;
- les deux chemins résolvent les **mêmes** objets ;
- le pipeline a quitté le core : ``core/uploads`` ne contient plus de logique I/O.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_UPLOADS = PROJECT_ROOT / "core" / "uploads"
FILES_PKG = PROJECT_ROOT / "packages" / "forge-mvc-files" / "forge_mvc_files"

PUBLIC_API = (
    "save_upload",
    "serve_media_file",
    "delete_upload",
    "delete_media_file",
    "get_upload_path",
    "SavedUpload",
    "save_bytes",
    "normalize_media_path",
    "is_upload_rate_limited",
)


class TestRealCodeInForgeFiles:
    @pytest.mark.parametrize("mod", ["manager.py", "storage.py", "rate_limit.py"])
    def test_module_present(self, mod):
        assert (FILES_PKG / mod).exists()

    def test_manager_has_save_upload_logic(self):
        text = (FILES_PKG / "manager.py").read_text(encoding="utf-8")
        assert "def save_upload" in text
        assert "def serve_media_file" in text

    def test_storage_has_antitraversal_logic(self):
        text = (FILES_PKG / "storage.py").read_text(encoding="utf-8")
        assert "def save_bytes" in text
        assert "def normalize_media_path" in text

    @pytest.mark.parametrize("name", PUBLIC_API)
    def test_public_api_exposed(self, name):
        import forge_mvc_files

        assert hasattr(forge_mvc_files, name)


class TestCoreUploadsAreShims:
    @pytest.mark.parametrize("mod", ["manager.py", "storage.py", "rate_limit.py"])
    def test_is_reexport_shim(self, mod):
        text = (CORE_UPLOADS / mod).read_text(encoding="utf-8")
        assert "forge_mvc_files" in text, f"{mod} doit réexporter forge_mvc_files."

    def test_no_io_logic_left_in_core_shims(self):
        # Les shims ne (re)définissent aucune fonction d'I/O.
        for mod in ("manager.py", "storage.py", "rate_limit.py"):
            text = (CORE_UPLOADS / mod).read_text(encoding="utf-8")
            assert "def save_upload" not in text
            assert "def save_bytes" not in text

    def test_shim_and_files_resolve_same_objects(self):
        import core.uploads.manager as shim_m
        import core.uploads.storage as shim_s
        import forge_mvc_files.manager as files_m
        import forge_mvc_files.storage as files_s

        assert shim_m.save_upload is files_m.save_upload
        assert shim_m.serve_media_file is files_m.serve_media_file
        assert shim_s.save_bytes is files_s.save_bytes

    def test_core_uploads_init_still_works(self):
        # Le shim de paquet réexporte toujours l'API (transparent).
        from core.uploads import save_upload, serve_media_file  # noqa: F401
        import forge_mvc_files

        assert save_upload is forge_mvc_files.save_upload


class TestPipelineLeftCore:
    def test_manager_source_in_files_not_core(self):
        import core.uploads.manager as shim

        # save_upload re-exporté : sa source réelle est dans forge_mvc_files.
        src_file = inspect.getsourcefile(shim.save_upload)
        assert "forge_mvc_files" in src_file
        assert "core/uploads" not in src_file
