"""Garde-fou FILES-VALIDATORS-KEEP-001 (ADR-019).

La validation **pure** de fichier (validators + exceptions ``UploadError``)
reste dans le core mais quitte ``core/uploads/`` (qui partira vers
``forge-mvc-files``) pour ``core/forms`` :

- ``core/forms/upload_validation.py`` et ``core/forms/upload_exceptions.py``
  contiennent l'implémentation réelle ;
- ``core/forms/fields.py`` (``FileField``) n'importe plus depuis
  ``core/uploads`` — il pourra survivre à la suppression de ``core/uploads`` ;
- ``core/uploads/validators.py`` et ``exceptions.py`` ne sont plus que des
  **shims** réexportant le core (supprimés au ticket ``CORE-DROP-UPLOADS-001``) ;
- les deux chemins d'import résolvent les **mêmes** objets (shim transparent).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIELDS = PROJECT_ROOT / "core" / "forms" / "fields.py"
NEW_VALIDATION = PROJECT_ROOT / "core" / "forms" / "upload_validation.py"
NEW_EXCEPTIONS = PROJECT_ROOT / "core" / "forms" / "upload_exceptions.py"
SHIM_VALIDATORS = PROJECT_ROOT / "core" / "uploads" / "validators.py"
SHIM_EXCEPTIONS = PROJECT_ROOT / "core" / "uploads" / "exceptions.py"

_VALIDATORS = (
    "validate_extension",
    "validate_mime_type",
    "validate_size",
    "validate_upload_metadata",
)
_EXCEPTIONS = (
    "UploadError",
    "UploadTooLargeError",
    "UploadInvalidExtensionError",
    "UploadInvalidMimeTypeError",
    "UploadStorageError",
)


class TestRealCodeInCore:
    def test_new_modules_exist(self):
        assert NEW_VALIDATION.exists()
        assert NEW_EXCEPTIONS.exists()

    def test_validation_has_real_logic(self):
        text = NEW_VALIDATION.read_text(encoding="utf-8")
        assert "def validate_upload_metadata" in text
        assert "Extension non autorisee" in text

    @pytest.mark.parametrize("name", _VALIDATORS)
    def test_validators_importable_from_core_forms(self, name):
        import core.forms.upload_validation as mod

        assert callable(getattr(mod, name))

    @pytest.mark.parametrize("name", _EXCEPTIONS)
    def test_exceptions_importable_from_core_forms(self, name):
        import core.forms.upload_exceptions as mod

        assert issubclass(getattr(mod, name), Exception)


class TestFieldsDecoupledFromUploads:
    def test_fields_does_not_import_core_uploads(self):
        text = FIELDS.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            assert "core.uploads" not in stripped, (
                "core/forms/fields.py ne doit plus importer core.uploads "
                f"(validation relocalisée) — vu : {line!r}"
            )

    def test_filefield_still_validates(self):
        # FileField fonctionne sans core.uploads (validation via core.forms).
        from core.forms.upload_exceptions import UploadInvalidExtensionError
        from core.forms.upload_validation import validate_extension

        with pytest.raises(UploadInvalidExtensionError):
            validate_extension("x.exe", ["png"])
        assert validate_extension("photo.PNG", ["png"]) == "png"


class TestUploadsModulesRemoved:
    """CORE-DROP-UPLOADS-001 (ADR-019) : les shims core/uploads ont disparu.

    La validation (validators + exceptions) vit dans core/forms ; le reste est
    parti vers forge-mvc-files. ``core.uploads`` n'existe plus.
    """

    @pytest.mark.parametrize("shim", [SHIM_VALIDATORS, SHIM_EXCEPTIONS])
    def test_shim_file_absent(self, shim):
        assert not shim.exists(), (
            f"{shim} doit avoir été supprimé (CORE-DROP-UPLOADS-001)."
        )

    def test_core_uploads_not_importable(self):
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("core.uploads.validators")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("core.uploads.exceptions")

    def test_validation_still_resolves_from_core_forms(self):
        import core.forms.upload_validation as new_v
        import core.forms.upload_exceptions as new_e

        for name in _VALIDATORS:
            assert callable(getattr(new_v, name))
        for name in _EXCEPTIONS:
            assert issubclass(getattr(new_e, name), Exception)
