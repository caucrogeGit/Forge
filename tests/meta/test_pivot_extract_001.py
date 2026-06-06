"""Tests PIVOT-EXTRACT-001 : pivot advanced deplace dans forge-mvc-pivot (ADR-021)."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

_CURRENT_VERSION = tomllib.loads(
    (Path(__file__).parent.parent.parent / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["version"]
pytest.importorskip("forge_mvc_pivot")

pytestmark = pytest.mark.meta


class TestPivotModuleAvailable:
    def test_can_import_public_api(self):
        from forge_mvc_pivot import (  # noqa: F401
            PivotAdvancedService,
            PivotConstraintError,
            PivotFieldConstraint,
            PivotFormError,
            PivotRow,
            pivot_error_to_form_error,
        )
        assert PivotAdvancedService is not None

    def test_module_has_version(self):
        import forge_mvc_pivot
        assert hasattr(forge_mvc_pivot, "__version__")
        assert forge_mvc_pivot.__version__ == _CURRENT_VERSION

    def test_all_exports_complete(self):
        import forge_mvc_pivot
        expected = {
            "PivotAdvancedService", "PivotConstraintError",
            "PivotFieldConstraint", "PivotFormError", "PivotRow",
            "pivot_error_to_form_error",
        }
        assert expected.issubset(set(forge_mvc_pivot.__all__))

    def test_generator_importable(self):
        from forge_mvc_pivot.make_pivot_crud import (  # noqa: F401
            cmd_make_pivot_crud_main,
            make_pivot_crud,
        )
        assert make_pivot_crud is not None


class TestPivotRemovedFromCore:
    def test_no_pivot_advanced_in_core(self):
        assert not Path("core/pivot_advanced.py").exists(), (
            "core/pivot_advanced.py aurait du etre supprime"
        )

    def test_no_make_pivot_crud_in_forge_cli(self):
        assert not Path("forge_cli/entities/make_pivot_crud.py").exists(), (
            "forge_cli/entities/make_pivot_crud.py aurait du etre supprime"
        )

    def test_old_service_import_fails(self):
        with pytest.raises(ImportError):
            import core.pivot_advanced  # noqa: F401

    def test_old_generator_import_fails(self):
        with pytest.raises(ImportError):
            import forge_cli.entities.make_pivot_crud  # noqa: F401


class TestNoCorePivotImportsRemain:
    @pytest.mark.parametrize("forbidden_import", [
        "from core.pivot_advanced",
        "import core.pivot_advanced",
        "forge_cli.entities.make_pivot_crud",
    ])
    def test_no_forbidden_imports(self, forbidden_import):
        this_file = Path(__file__).resolve()
        roots = [Path("core"), Path("mvc"), Path("forge_cli"), Path("tests")]
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if py_file.resolve() == this_file:
                    continue
                if forbidden_import in py_file.read_text(encoding="utf-8"):
                    offenders.append(str(py_file))
        assert not offenders, (
            f"References a l'ancien chemin pivot restantes dans : {offenders}"
        )


class TestPivotFunctional:
    def test_attach_then_get(self):
        from forge_mvc_pivot import PivotAdvancedService

        rows: list[dict] = []

        def fake_insert(sql, params):
            rows.append(dict(zip(("article_id", "tag_id", "position"), params)))
            return len(rows)

        def fake_fetch_one(sql, params):
            for r in rows:
                if r["article_id"] == params[0] and r["tag_id"] == params[1]:
                    return r
            return None

        svc = PivotAdvancedService(
            "article_tag", "article_id", "tag_id", ["position"],
            insert_fn=fake_insert, fetch_one=fake_fetch_one,
        )
        svc.attach(1, 2, {"position": 5})
        row = svc.get(1, 2)
        assert row is not None
        assert row.pivot_data == {"position": 5}

    def test_unknown_field_rejected(self):
        from forge_mvc_pivot import PivotAdvancedService

        svc = PivotAdvancedService(
            "article_tag", "article_id", "tag_id", ["position"],
            insert_fn=lambda s, p: 1,
        )
        with pytest.raises(ValueError):
            svc.attach(1, 2, {"inconnu": "x"})


class TestPyprojectMetadata:
    def test_pyproject_version(self):
        content = Path("packages/forge-mvc-pivot/pyproject.toml").read_text(encoding="utf-8")
        assert f'version = "{_CURRENT_VERSION}"' in content

    def test_forge_mvc_dependency_declared(self):
        content = Path("packages/forge-mvc-pivot/pyproject.toml").read_text(encoding="utf-8")
        assert "forge-mvc>=" in content
