"""Garde-fou CORE-RBAC-PLUGIN-MECHANISM-001.

Vérifie que le core ne nomme plus nominalement forge_mvc_rbac (charte principe 8)
et que le pattern push (registre de fournisseurs Jinja) est en place.

Architecture :
- core/mvc/controller/registry.py : registre push
- forge_mvc_rbac/__init__.py : s'enregistre lui-même via try/except ImportError
- BaseController.render() : itère sur iter_jinja_context_providers()
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_CTRL = PROJECT_ROOT / "core" / "mvc" / "controller" / "base_controller.py"
REGISTRY = PROJECT_ROOT / "core" / "mvc" / "controller" / "registry.py"
CTRL_BUILDER = PROJECT_ROOT / "forge_cli" / "entities" / "crud" / "controller_builder.py"


# ---------------------------------------------------------------------------
# Classe 1 — Existence du module registre
# ---------------------------------------------------------------------------

class TestRegistryModuleExists:

    def test_registry_file_exists(self):
        assert REGISTRY.is_file(), "core/mvc/controller/registry.py doit exister"

    def test_register_function_exported(self):
        from core.mvc.controller.registry import register_jinja_context_provider
        assert callable(register_jinja_context_provider)

    def test_iter_function_exported(self):
        from core.mvc.controller.registry import iter_jinja_context_providers
        assert callable(iter_jinja_context_providers)

    def test_clear_function_exported(self):
        from core.mvc.controller.registry import _clear_for_tests
        assert callable(_clear_for_tests)

    def test_registry_re_exported_from_controller_package(self):
        from core.mvc.controller import register_jinja_context_provider, iter_jinja_context_providers
        assert callable(register_jinja_context_provider)
        assert callable(iter_jinja_context_providers)


# ---------------------------------------------------------------------------
# Classe 2 — Comportement du registre
# ---------------------------------------------------------------------------

class TestRegistryBehavior:

    def setup_method(self):
        from core.mvc.controller.registry import _clear_for_tests, iter_jinja_context_providers
        self._saved = list(iter_jinja_context_providers())
        _clear_for_tests()

    def teardown_method(self):
        from core.mvc.controller.registry import _clear_for_tests, register_jinja_context_provider
        _clear_for_tests()
        for fn in self._saved:
            register_jinja_context_provider(fn)

    def test_register_and_iter(self):
        from core.mvc.controller.registry import iter_jinja_context_providers, register_jinja_context_provider

        def fn(req):
            return {"x": 1}

        register_jinja_context_provider(fn)
        assert fn in iter_jinja_context_providers()

    def test_multiple_providers(self):
        from core.mvc.controller.registry import iter_jinja_context_providers, register_jinja_context_provider

        def fn1(req):
            return {"a": 1}

        def fn2(req):
            return {"b": 2}

        register_jinja_context_provider(fn1)
        register_jinja_context_provider(fn2)
        providers = iter_jinja_context_providers()
        assert fn1 in providers
        assert fn2 in providers

    def test_clear_empties_registry(self):
        from core.mvc.controller.registry import (
            _clear_for_tests,
            iter_jinja_context_providers,
            register_jinja_context_provider,
        )

        def fn(req):
            return {}

        register_jinja_context_provider(fn)
        _clear_for_tests()
        assert iter_jinja_context_providers() == []

    def test_iter_returns_copy(self):
        from core.mvc.controller.registry import iter_jinja_context_providers, register_jinja_context_provider

        def fn(req):
            return {}

        register_jinja_context_provider(fn)
        copy1 = iter_jinja_context_providers()
        copy2 = iter_jinja_context_providers()
        assert copy1 is not copy2

    def test_provider_called_on_ctx_update(self):
        from core.mvc.controller.registry import iter_jinja_context_providers, register_jinja_context_provider

        class FakeRequest:
            pass

        def provider(req):
            return {"injected": True}

        register_jinja_context_provider(provider)
        ctx = {}
        for provider in iter_jinja_context_providers():
            ctx.update(provider(FakeRequest()))
        assert ctx.get("injected") is True


# ---------------------------------------------------------------------------
# Classe 3 — Core ne nomme plus forge_mvc_rbac nominalement
# ---------------------------------------------------------------------------

class TestCoreNominalImportAbsent:

    def test_base_controller_no_forge_mvc_rbac_import(self):
        src = BASE_CTRL.read_text(encoding="utf-8")
        assert "forge_mvc_rbac" not in src, (
            "base_controller.py contient encore 'forge_mvc_rbac'. "
            "Le core ne doit pas nommer nominalement les modules opt-in (charte principe 8). "
            "Utiliser le registre iter_jinja_context_providers() à la place."
        )

    def test_base_controller_uses_registry(self):
        src = BASE_CTRL.read_text(encoding="utf-8")
        assert "iter_jinja_context_providers" in src, (
            "base_controller.py doit utiliser iter_jinja_context_providers() du registre."
        )


# ---------------------------------------------------------------------------
# Classe 4 — forge_mvc_rbac s'auto-enregistre (import conditionnel)
# ---------------------------------------------------------------------------

class TestRbacSelfRegisters:

    def test_rbac_init_contains_self_registration(self):
        import forge_mvc_rbac
        src = Path(forge_mvc_rbac.__file__).read_text(encoding="utf-8")
        assert "register_jinja_context_provider" in src, (
            "forge_mvc_rbac/__init__.py doit contenir register_jinja_context_provider."
        )

    def test_rbac_registration_is_conditional(self):
        import forge_mvc_rbac
        src = Path(forge_mvc_rbac.__file__).read_text(encoding="utf-8")
        assert "ImportError" in src, (
            "La self-registration de forge_mvc_rbac doit être dans un try/except ImportError."
        )

    def test_rbac_registers_with_can_wrapper(self):
        import forge_mvc_rbac
        src = Path(forge_mvc_rbac.__file__).read_text(encoding="utf-8")
        assert "make_auth_jinja_context_with_can" in src, (
            "forge_mvc_rbac doit enregistrer make_auth_jinja_context_with_can."
        )

    def test_rbac_wrapper_exported(self):
        from forge_mvc_rbac import make_auth_jinja_context_with_can
        assert callable(make_auth_jinja_context_with_can)


# ---------------------------------------------------------------------------
# Classe 5 — controller_builder.py : import RBAC conditionnel (R8 confirmé)
# ---------------------------------------------------------------------------

class TestControllerBuilderRbacImportIsConditional:

    def test_rbac_import_inside_conditional(self):
        src = CTRL_BUILDER.read_text(encoding="utf-8")
        assert "if _rbac" in src, (
            "controller_builder.py doit conditionner l'import forge_mvc_rbac à _rbac."
        )

    def test_forge_mvc_rbac_present_in_builder(self):
        src = CTRL_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_rbac" in src, (
            "controller_builder.py doit référencer forge_mvc_rbac (CLI code-gen conditionnel)."
        )
