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

import inspect
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


class TestUploadsModulesAreShims:
    @pytest.mark.parametrize("shim", [SHIM_VALIDATORS, SHIM_EXCEPTIONS])
    def test_is_reexport_shim(self, shim):
        text = shim.read_text(encoding="utf-8")
        assert "core.forms.upload_" in text, f"{shim.name} doit réexporter core.forms."
        # Pas de logique propre (les fonctions ne sont pas (re)définies ici).
        assert "def validate_extension" not in text or shim is None

    def test_shim_and_core_resolve_same_objects(self):
        import core.forms.upload_validation as new_v
        import core.forms.upload_exceptions as new_e
        import core.uploads.validators as shim_v
        import core.uploads.exceptions as shim_e

        for name in _VALIDATORS:
            assert getattr(shim_v, name) is getattr(new_v, name)
        for name in _EXCEPTIONS:
            assert getattr(shim_e, name) is getattr(new_e, name)

    def test_validators_shim_has_no_real_logic(self):
        # Le shim ne (re)définit aucune fonction : il importe seulement.
        import core.uploads.validators as shim_v

        src = inspect.getsource(shim_v)
        assert "def validate_extension" not in src
