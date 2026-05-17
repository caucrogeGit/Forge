"""Tests WORKFLOW-EXTRACT-001 : workflow deplace dans forge-mvc-workflow."""
from __future__ import annotations

from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_workflow")

pytestmark = pytest.mark.meta


class TestWorkflowModuleAvailable:
    def test_can_import_public_api(self):
        from forge_mvc_workflow import (  # noqa: F401
            WorkflowStatus,
            WorkflowStatusError,
            WorkflowTransition,
            WorkflowTransitionError,
            can_transition,
            find_status,
            get_available_transitions,
            make_status,
            make_transition,
            make_workflow_jinja_helpers,
            normalize_status_name,
            validate_status_name,
            validate_statuses,
            validate_transitions,
            workflow_status_badge,
            workflow_status_badge_class,
            workflow_status_color,
            workflow_status_label,
        )
        assert WorkflowStatus is not None

    def test_module_has_version(self):
        import forge_mvc_workflow
        assert hasattr(forge_mvc_workflow, "__version__")
        assert forge_mvc_workflow.__version__ == "1.0.0b4"

    def test_all_exports_complete(self):
        import forge_mvc_workflow
        expected = {
            "WorkflowStatus", "WorkflowStatusError",
            "WorkflowTransition", "WorkflowTransitionError",
            "can_transition", "find_status", "get_available_transitions",
            "make_status", "make_transition", "make_workflow_jinja_helpers",
            "normalize_status_name", "validate_status_name",
            "validate_statuses", "validate_transitions",
            "workflow_status_badge", "workflow_status_badge_class",
            "workflow_status_color", "workflow_status_label",
        }
        assert expected.issubset(set(forge_mvc_workflow.__all__))


class TestWorkflowRemovedFromCore:
    def test_no_workflow_dir_in_core(self):
        assert not Path("core/workflow").exists(), (
            "core/workflow/ aurait du etre supprime"
        )

    def test_old_import_fails(self):
        with pytest.raises(ImportError):
            import core.workflow  # noqa: F401


class TestNoCoreWorkflowImportsRemain:
    @pytest.mark.parametrize("forbidden_import", [
        "from core.workflow",
        "import core.workflow",
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
                content = py_file.read_text(encoding="utf-8")
                if forbidden_import in content:
                    offenders.append(str(py_file))
        assert not offenders, (
            f"Imports core.workflow restants dans : {offenders}"
        )


class TestWorkflowFunctional:
    def test_status_cycle_de_vie(self):
        from forge_mvc_workflow import (
            can_transition,
            make_status,
            make_transition,
            validate_statuses,
            validate_transitions,
        )
        statuses = validate_statuses([
            make_status("brouillon"),
            make_status("confirme"),
            make_status("annule"),
        ])
        transitions = validate_transitions([
            make_transition("brouillon", "confirme"),
            make_transition("brouillon", "annule"),
        ], statuses=statuses)
        assert can_transition(transitions, "brouillon", "confirme")
        assert not can_transition(transitions, "confirme", "brouillon")

    def test_jinja_helpers_retourne_dict(self):
        from forge_mvc_workflow import make_workflow_jinja_helpers
        helpers = make_workflow_jinja_helpers()
        assert isinstance(helpers, dict)
        assert "workflow_status_badge" in helpers


class TestPyprojectMetadata:
    def test_pyproject_version(self):
        content = Path("packages/forge-mvc-workflow/pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "1.0.0b4"' in content

    def test_markupsafe_dependency_declared(self):
        content = Path("packages/forge-mvc-workflow/pyproject.toml").read_text(encoding="utf-8")
        assert "markupsafe" in content.lower()
