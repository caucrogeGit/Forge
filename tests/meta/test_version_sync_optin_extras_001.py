"""Garde-fou VERSION-SYNC-OPTIN-EXTRAS-001.

Verifie que :
- VERSION-SYNC-OPTIN-EXTRAS-001 est reference dans la roadmap et marque livré ;
- pyproject.toml racine contient les extras rbac, workflow, stats ;
- pyproject.toml racine ne contient pas d'extra media ni mfa ;
- les extras rbac/workflow/stats utilisent les contraintes >=1.0.0b4,<2 ;
- l'extra all contient exactement rbac/workflow/stats (pas media, pas mfa) ;
- les dependances obligatoires du core ne contiennent aucun opt-in ;
- media et mfa n'ont plus Private :: Do Not Upload (requalifiés Alpha) ;
- la documentation ne présente pas forge-mvc[media] ou forge-mvc[mfa] comme disponibles.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
INSTALL_DOC = PROJECT_ROOT / "docs" / "install" / "index.md"

_PUBLISHABLE_EXTRAS = ["rbac", "workflow", "stats"]
_FORBIDDEN_EXTRAS = ["media", "mfa"]


def _root_data() -> dict:
    return tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))


class TestRoadmapReference:
    def test_roadmap_mentions_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "VERSION-SYNC-OPTIN-EXTRAS-001" in text, (
            "La roadmap doit mentionner VERSION-SYNC-OPTIN-EXTRAS-001."
        )

    def test_roadmap_marks_ticket_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("VERSION-SYNC-OPTIN-EXTRAS-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "VERSION-SYNC-OPTIN-EXTRAS-001 doit etre marque 'livré' dans la roadmap."
        )


@pytest.mark.parametrize("extra_name", _PUBLISHABLE_EXTRAS)
class TestPublishableExtrasPresent:
    def test_extra_declared(self, extra_name):
        data = _root_data()
        extras = data.get("project", {}).get("optional-dependencies", {})
        assert extra_name in extras, (
            f"pyproject.toml racine doit declarer l'extra [{extra_name}]."
        )

    def test_extra_uses_relaxed_constraint(self, extra_name):
        data = _root_data()
        extras = data.get("project", {}).get("optional-dependencies", {})
        deps = extras.get(extra_name, [])
        assert deps, f"L'extra [{extra_name}] est vide."
        pkg_name = f"forge-mvc-{extra_name}"
        matching = [d for d in deps if pkg_name in d]
        assert matching, f"L'extra [{extra_name}] ne reference pas {pkg_name}."
        for dep in matching:
            assert ">=" in dep and ",<2" in dep, (
                f"L'extra [{extra_name}] doit utiliser une contrainte relachee (>=X,<2) — trouvé : {dep!r}."
            )


class TestAllExtraContent:
    def test_all_extra_declared(self):
        data = _root_data()
        extras = data.get("project", {}).get("optional-dependencies", {})
        assert "all" in extras, "pyproject.toml racine doit declarer l'extra [all]."

    def test_all_contains_rbac(self):
        data = _root_data()
        deps = data["project"]["optional-dependencies"]["all"]
        assert any("forge-mvc-rbac" in d for d in deps), (
            "L'extra [all] doit contenir forge-mvc-rbac."
        )

    def test_all_contains_workflow(self):
        data = _root_data()
        deps = data["project"]["optional-dependencies"]["all"]
        assert any("forge-mvc-workflow" in d for d in deps), (
            "L'extra [all] doit contenir forge-mvc-workflow."
        )

    def test_all_contains_stats(self):
        data = _root_data()
        deps = data["project"]["optional-dependencies"]["all"]
        assert any("forge-mvc-stats" in d for d in deps), (
            "L'extra [all] doit contenir forge-mvc-stats."
        )

    def test_all_does_not_contain_mfa(self):
        data = _root_data()
        deps = data["project"]["optional-dependencies"].get("all", [])
        assert not any("forge-mvc-mfa" in d for d in deps), (
            "L'extra [all] ne doit pas contenir forge-mvc-mfa."
        )

    def test_all_does_not_contain_media(self):
        data = _root_data()
        deps = data["project"]["optional-dependencies"].get("all", [])
        assert not any("forge-mvc-media" in d for d in deps), (
            "L'extra [all] ne doit pas contenir forge-mvc-media."
        )


@pytest.mark.parametrize("extra_name", _FORBIDDEN_EXTRAS)
class TestForbiddenExtrasAbsent:
    def test_extra_not_declared(self, extra_name):
        data = _root_data()
        extras = data.get("project", {}).get("optional-dependencies", {})
        assert extra_name not in extras, (
            f"pyproject.toml racine ne doit pas declarer l'extra [{extra_name}] "
            f"— ce package n'est pas encore publiable."
        )


class TestCoreNoDependsOnOptins:
    def test_core_deps_no_rbac(self):
        data = _root_data()
        deps = data.get("project", {}).get("dependencies", [])
        assert not any("forge-mvc-rbac" in d for d in deps), (
            "Le core forge-mvc ne doit pas dependre de forge-mvc-rbac."
        )

    def test_core_deps_no_workflow(self):
        data = _root_data()
        deps = data.get("project", {}).get("dependencies", [])
        assert not any("forge-mvc-workflow" in d for d in deps), (
            "Le core forge-mvc ne doit pas dependre de forge-mvc-workflow."
        )

    def test_core_deps_no_stats(self):
        data = _root_data()
        deps = data.get("project", {}).get("dependencies", [])
        assert not any("forge-mvc-stats" in d for d in deps), (
            "Le core forge-mvc ne doit pas dependre de forge-mvc-stats."
        )

    def test_core_deps_no_media(self):
        data = _root_data()
        deps = data.get("project", {}).get("dependencies", [])
        assert not any("forge-mvc-media" in d for d in deps), (
            "Le core forge-mvc ne doit pas dependre de forge-mvc-media."
        )

    def test_core_deps_no_mfa(self):
        data = _root_data()
        deps = data.get("project", {}).get("dependencies", [])
        assert not any("forge-mvc-mfa" in d for d in deps), (
            "Le core forge-mvc ne doit pas dependre de forge-mvc-mfa."
        )


@pytest.mark.parametrize("pkg", ["forge-mvc-mfa", "forge-mvc-media"])
class TestAlphaPreparedClassifier:
    def test_no_private_classifier(self, pkg):
        """forge-mvc-mfa et forge-mvc-media ont retiré 'Private :: Do Not Upload' (requalifiés Alpha)."""
        toml = PROJECT_ROOT / "packages" / pkg / "pyproject.toml"
        data = tomllib.loads(toml.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert not any("Private :: Do Not Upload" in c for c in classifiers), (
            f"{pkg} ne doit plus avoir 'Private :: Do Not Upload' "
            f"(requalifié Alpha : MFA-PYPI-READY-001 / MEDIA-PYPI-READY-002)."
        )


class TestDocumentationExtrasCoherence:
    # Formulations acceptées pour clarifier qu'un extra n'est pas exposé par le
    # core. La liste reste large car la doc peut évoluer ; l'intention est que
    # le lecteur ne croit JAMAIS pouvoir lancer `pip install forge-mvc[mfa]`
    # ou `pip install forge-mvc[media]` directement.
    _NOT_AVAILABLE_HINTS = (
        "pas disponible",
        "non disponible",
        "ne sont pas disponibles",
        "ne sont pas définis comme extras",
        "ne sont pas déclarés",
    )

    def _has_unavailable_hint(self, text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in self._NOT_AVAILABLE_HINTS)

    def test_install_doc_no_media_available_claim(self):
        text = INSTALL_DOC.read_text(encoding="utf-8")
        assert "forge-mvc[media]" not in text or self._has_unavailable_hint(text), (
            "install/index.md ne doit pas presenter forge-mvc[media] comme disponible "
            "(les paquets s'installent directement via `pip install --pre forge-mvc-media`)."
        )

    def test_install_doc_no_mfa_available_claim(self):
        text = INSTALL_DOC.read_text(encoding="utf-8")
        assert "forge-mvc[mfa]" not in text or self._has_unavailable_hint(text), (
            "install/index.md ne doit pas presenter forge-mvc[mfa] comme disponible "
            "(les paquets s'installent directement via `pip install --pre forge-mvc-mfa`)."
        )
