"""Tests — OPTINS-IOT-PROJECT-BRIDGE-001.

Vérifie que le starter `welcome-iot` applique concrètement la convention
`optins/` (contrat figé par OPTINS-PROJECT-STRUCTURE-001) au cas Forge
IoT :

- le starter livre une couche `optins/` (registry + iot/) ;
- `optins/registry.py` expose `register_optins(router)` et délègue à
  `optins/iot/routes.py` ;
- `optins/iot/routes.py` appelle `register_iot_routes` (API publique du
  paquet `forge-mvc-iot`) ;
- `mvc/routes.py` (via le snippet) appelle `register_optins(router)` et
  **ne** branche **pas** l'API IoT en direct ;
- aucune découverte automatique (pas de scan / import dynamique) ;
- `forge_mvc_iot` n'est importé **que** dans la couche opt-in ;
- `core/` n'importe toujours pas `forge_mvc_iot` ;
- la doc du starter et la roadmap mentionnent le modèle.

Tests **statiques** : on lit les fichiers livrés par le starter, on
n'exécute aucun flux IoT.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STARTER = _REPO_ROOT / "forge_cli" / "starters" / "data" / "welcome-iot"
_FILES = _STARTER / "files"
_OPTINS = _FILES / "optins"
_SNIPPET = _STARTER / "routes.py.snippet"
_DOC = _REPO_ROOT / "docs" / "starters" / "welcome-iot" / "index.md"
_ARCH_DOC = _REPO_ROOT / "docs" / "architecture" / "optins-project-structure.md"
_ROADMAP = _REPO_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
_CORE_DIR = _REPO_ROOT / "core"


# ── 1. Structure optins/ générée par le starter ─────────────────────────────


class TestOptinsStructure:
    @pytest.mark.parametrize(
        "rel",
        [
            "__init__.py",
            "registry.py",
            "iot/__init__.py",
            "iot/routes.py",
            "iot/README.md",
            "iot/migrations/README.md",
        ],
    )
    def test_optins_file_present(self, rel):
        assert (_OPTINS / rel).exists(), (
            f"Le starter welcome-iot doit livrer optins/{rel}"
        )


# ── 2. Registre explicite ───────────────────────────────────────────────────


class TestRegistry:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = (_OPTINS / "registry.py").read_text(encoding="utf-8")

    def test_defines_register_optins(self):
        assert "def register_optins(router)" in self.text

    def test_delegates_to_iot_routes(self):
        assert "from optins.iot.routes import register" in self.text
        assert "register_iot(router)" in self.text

    def test_no_magic_discovery(self):
        # Pas de scan automatique de modules / plugins.
        lowered = self.text.lower()
        for forbidden in ("importlib", "pkgutil", "iter_modules", "glob", "walk_packages"):
            assert forbidden not in lowered, forbidden


# ── 3. Branchement IoT ──────────────────────────────────────────────────────


class TestIotRoutesBridge:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = (_OPTINS / "iot" / "routes.py").read_text(encoding="utf-8")

    def test_imports_register_iot_routes(self):
        assert "from forge_mvc_iot import register_iot_routes" in self.text

    def test_defines_register_and_calls_iot(self):
        assert "def register(router)" in self.text
        assert "register_iot_routes(router)" in self.text


# ── 4. Snippet mvc/routes.py ────────────────────────────────────────────────


class TestRoutesSnippetBranchesOptins:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = _SNIPPET.read_text(encoding="utf-8")

    def test_calls_register_optins(self):
        assert "from optins.registry import register_optins" in self.text
        assert "register_optins(router)" in self.text

    def test_does_not_branch_iot_directly(self):
        # Le branchement direct a migré vers optins/iot/routes.py.
        assert "from forge_mvc_iot import register_iot_routes" not in self.text


# ── 5. Périmètre : forge_mvc_iot seulement côté opt-in ──────────────────────


class TestForgeMvcIotConfinedToOptin:
    def test_iot_import_only_in_optins_layer(self):
        # Dans les fichiers livrés par le starter, `forge_mvc_iot` ne doit
        # apparaître que sous optins/ (le contrôleur pédagogique l'importe
        # aussi, mais le *branchement de routes* passe par optins/).
        offenders: list[str] = []
        for py in _FILES.rglob("*.py"):
            rel = py.relative_to(_FILES)
            if "register_iot_routes" in py.read_text(encoding="utf-8"):
                if rel.parts[0] != "optins":
                    offenders.append(str(rel))
        assert not offenders, (
            f"register_iot_routes ne doit être branché que sous optins/ : {offenders}"
        )

    def test_core_does_not_import_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in _CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders


# ── 6. README local court (pas de duplication de la doc officielle) ─────────


class TestLocalReadme:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = (_OPTINS / "iot" / "README.md").read_text(encoding="utf-8")

    def test_mentions_api_routes(self):
        assert "/api/iot/events" in self.text

    def test_points_to_official_docs(self):
        assert "forgemvc.com/docs/forge/iot" in self.text

    def test_stays_short(self):
        # README local = utile et court, pas une copie de la doc officielle.
        assert len(self.text.splitlines()) < 60


# ── 7. Documentation & roadmap ──────────────────────────────────────────────


class TestDocs:
    def test_starter_doc_mentions_optins(self):
        text = _DOC.read_text(encoding="utf-8")
        assert "optins/" in text
        assert "register_optins" in text

    def test_architecture_doc_references_welcome_iot(self):
        text = _ARCH_DOC.read_text(encoding="utf-8")
        assert "welcome-iot" in text

    def test_roadmap_mentions_ticket(self):
        assert "OPTINS-IOT-PROJECT-BRIDGE-001" in _ROADMAP.read_text(encoding="utf-8")
