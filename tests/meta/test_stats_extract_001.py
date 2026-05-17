"""Tests STATS-EXTRACT-001 : stats déplacé dans forge-mvc-stats."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

_CURRENT_VERSION = tomllib.loads((Path(__file__).parent.parent.parent / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
pytest.importorskip("forge_mvc_stats")

pytestmark = pytest.mark.meta


class TestStatsModuleAvailable:
    def test_can_import_public_api(self):
        from forge_mvc_stats import (  # noqa: F401
            STATS_EVENTS_COLUMNS,
            STATS_EVENTS_TABLE,
            StatsAdminError,
            StatsEvent,
            StatsEventError,
            get_stats_events_admin_sql,
            get_stats_events_schema_sql,
            get_track_event_sql,
            list_stats_events,
            make_event,
            normalize_event_name,
            normalize_stats_event_row,
            prepare_stats_events_admin_params,
            prepare_track_event_values,
            track_event,
            validate_event,
            validate_event_name,
        )
        assert StatsEvent is not None

    def test_module_has_version(self):
        import forge_mvc_stats
        assert hasattr(forge_mvc_stats, "__version__")
        assert forge_mvc_stats.__version__ == _CURRENT_VERSION

    def test_all_exports_complete(self):
        import forge_mvc_stats
        expected = {
            "StatsEvent", "StatsEventError",
            "normalize_event_name", "validate_event_name", "make_event", "validate_event",
            "STATS_EVENTS_TABLE", "STATS_EVENTS_COLUMNS", "get_stats_events_schema_sql",
            "get_track_event_sql", "prepare_track_event_values", "track_event",
            "StatsAdminError", "get_stats_events_admin_sql",
            "prepare_stats_events_admin_params", "normalize_stats_event_row",
            "list_stats_events",
        }
        assert expected.issubset(set(forge_mvc_stats.__all__))


class TestStatsRemovedFromCore:
    def test_no_stats_dir_in_core(self):
        assert not Path("core/stats").exists(), (
            "core/stats/ aurait dû être supprimé"
        )

    def test_old_import_fails(self):
        with pytest.raises(ImportError):
            import core.stats  # noqa: F401


class TestNoCoreStatsImportsRemain:
    @pytest.mark.parametrize("forbidden_import", [
        "from core.stats",
        "import core.stats",
    ])
    def test_no_forbidden_imports(self, forbidden_import):
        this_file = Path(__file__).resolve()
        roots = [Path("core"), Path("mvc"), Path("forge_cli"), Path("tests"), Path("integrations")]
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if py_file.resolve() == this_file:
                    continue
                content = py_file.read_text(encoding="utf-8")
                if forbidden_import in content:
                    offenders.append(str(py_file))
        assert not offenders, (
            f"Imports core.stats restants dans : {offenders}"
        )


class TestStatsFunctional:
    def test_make_event_et_validate(self):
        from forge_mvc_stats import make_event, validate_event, validate_event_name
        evt = make_event("page_view", label="Accueil", category="navigation")
        assert evt.name == "page_view"
        validated = validate_event(evt)
        assert validate_event_name(validated.name) == "page_view"

    def test_schema_sql_retourne_create_table(self):
        from forge_mvc_stats import STATS_EVENTS_TABLE, get_stats_events_schema_sql
        sql = get_stats_events_schema_sql()
        assert "CREATE TABLE" in sql
        assert STATS_EVENTS_TABLE in sql

    def test_track_event_sql(self):
        from forge_mvc_stats import get_track_event_sql
        sql = get_track_event_sql()
        assert "INSERT INTO" in sql
        assert "forge_stats_events" in sql

    def test_list_stats_events_avec_fetch_stub(self):
        from forge_mvc_stats import list_stats_events
        rows = list_stats_events(lambda sql, params: [])
        assert rows == []


class TestPyprojectMetadata:
    def test_pyproject_version(self):
        content = Path("packages/forge-mvc-stats/pyproject.toml").read_text(encoding="utf-8")
        assert f'version = "{_CURRENT_VERSION}"' in content

    def test_description_updated(self):
        content = Path("packages/forge-mvc-stats/pyproject.toml").read_text(encoding="utf-8")
        assert "placeholder" not in content.lower()
