"""Tests — OPTINS-CLI-ENABLE-IOT-001.

Vérifie la commande `forge opt-in:enable iot` :

- dry-run par défaut (n'écrit rien) ;
- `--apply` crée la couche `optins/` (registry + iot/) ;
- idempotence (2e exécution sans doublon ni écrasement) ;
- fichier divergent → `[WARN]` + aucune écriture (+ exit 1 en --apply) ;
- paquet `forge-mvc-iot` absent → erreur claire (exit 1) ;
- opt-in inconnu → erreur claire (exit 2) ;
- `mvc/routes.py` n'est jamais modifié automatiquement ;
- aucune découverte magique dans le code généré ;
- `core/` n'importe toujours pas `forge_mvc_iot` ;
- enregistrement CLI (forge.py, help.py, help_dispatch).

Les tests unitaires appellent `enable_optin(..., project_root=tmp,
package_check=...)` — aucun fichier réel du dépôt n'est touché.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cli.optins.enable import SUPPORTED_OPTINS, enable_optin, main

_REPO_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = _REPO_ROOT / "forge.py"
HELP_FILE = _REPO_ROOT / "cli" / "_support" / "help.py"
ENABLE_FILE = _REPO_ROOT / "cli" / "optins" / "enable.py"
CORE_DIR = _REPO_ROOT / "core"

_PKG_OK = lambda _name: True  # noqa: E731 — paquet présent
_PKG_ABSENT = lambda _name: False  # noqa: E731 — paquet absent


_IOT_FILES = [
    "optins/__init__.py",
    "optins/registry.py",
    "optins/iot/__init__.py",
    "optins/iot/routes.py",
    "optins/iot/README.md",
    "optins/iot/migrations/README.md",
]


# ── Dry-run (défaut) ─────────────────────────────────────────────────────────


class TestDryRunDefault:
    def test_dry_run_writes_nothing(self, tmp_path, capsys):
        rc = enable_optin("iot", project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert not (tmp_path / "optins").exists()
        assert "[DRY-RUN]" in out
        assert "Aucune modification écrite" in out
        assert "--apply" in out

    def test_dry_run_lists_each_file(self, tmp_path, capsys):
        enable_optin("iot", project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        for rel in _IOT_FILES:
            assert f"{rel} serait créé" in out

    def test_dry_run_still_checks_package(self, tmp_path, capsys):
        rc = enable_optin("iot", project_root=tmp_path, package_check=_PKG_ABSENT)
        out = capsys.readouterr().out
        assert rc == 1
        assert "n'est pas installé" in out
        assert not (tmp_path / "optins").exists()


# ── Application réelle ───────────────────────────────────────────────────────


class TestApply:
    def test_apply_creates_all_files(self, tmp_path, capsys):
        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        out = capsys.readouterr().out
        assert rc == 0
        for rel in _IOT_FILES:
            assert (tmp_path / rel).exists(), rel
            assert f"{rel} créé" in out

    def test_registry_branches_iot(self, tmp_path):
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        registry = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
        assert "def register_optins(router: Router) -> None:" in registry
        assert "from optins.iot.routes import register" in registry

    def test_iot_routes_calls_register_iot_routes(self, tmp_path):
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        routes = (tmp_path / "optins" / "iot" / "routes.py").read_text(encoding="utf-8")
        assert "from forge_mvc_iot import register_iot_routes" in routes
        assert "register_iot_routes(router)" in routes

    def test_readme_is_short_and_points_to_package(self, tmp_path):
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        readme = (tmp_path / "optins" / "iot" / "README.md").read_text(encoding="utf-8")
        assert "pip install --pre forge-mvc-iot" in readme
        assert "forge iot:doctor" in readme
        assert len(readme.splitlines()) < 60


# ── Idempotence ──────────────────────────────────────────────────────────────


class TestIdempotence:
    def test_second_apply_no_duplicate(self, tmp_path, capsys):
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        capsys.readouterr()
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert "déjà présent" in out
        assert "créé" not in out  # rien de recréé
        # Le registre n'a pas de doublon d'appel register_iot.
        registry = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
        assert registry.count("register_iot(router)") == 1


# ── Conflit : fichier divergent ──────────────────────────────────────────────


class TestConflict:
    def test_divergent_file_is_not_overwritten(self, tmp_path, capsys):
        # Pré-crée un routes.py custom différent.
        target = tmp_path / "optins" / "iot" / "routes.py"
        target.parent.mkdir(parents=True)
        target.write_text("# custom user content\n", encoding="utf-8")

        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        out = capsys.readouterr().out
        # Conflit bloquant en --apply.
        assert rc == 1
        assert "[WARN]" in out
        assert "contenu différent" in out
        # Le fichier custom est préservé.
        assert target.read_text(encoding="utf-8") == "# custom user content\n"

    def test_divergent_file_dry_run_is_not_blocking(self, tmp_path, capsys):
        target = tmp_path / "optins" / "registry.py"
        target.parent.mkdir(parents=True)
        target.write_text("# custom\n", encoding="utf-8")
        rc = enable_optin("iot", project_root=tmp_path, package_check=_PKG_OK)
        capsys.readouterr()
        assert rc == 0  # dry-run ne bloque pas


# ── Erreurs ──────────────────────────────────────────────────────────────────


class TestErrors:
    def test_unknown_optin_exit_2(self, tmp_path, capsys):
        rc = enable_optin("rbac", project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 2
        assert "opt-in inconnu" in out
        assert not (tmp_path / "optins").exists()

    def test_missing_package_exit_1(self, tmp_path, capsys):
        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_ABSENT,
        )
        out = capsys.readouterr().out
        assert rc == 1
        assert "forge-mvc-iot" in out
        assert not (tmp_path / "optins").exists()

    def test_main_missing_name_exit_2(self, capsys):
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 2
        assert "manquant" in out


# ── mvc/routes/__init__.py : jamais modifié (ADR-085) ────────────────────────
#
# Le câblage en affichage seul est couvert en détail par
# tests/test_optins_cli_enable_routes_apply_001.py. Ici on garde le garde-fou
# « routes/__init__.py n'est jamais réécrit ».


class TestAmbiguousRoutesNotModified:
    def test_routes_py_jamais_modifie(self, tmp_path, capsys):
        # ADR-085 : routes/__init__.py n'est jamais modifié, quelle que soit
        # sa structure ; le branchement est seulement affiché.
        mvc = tmp_path / "mvc"
        (mvc / "routes").mkdir(parents=True)
        routes = mvc / "routes" / "__init__.py"
        original = "def register(router):\n    pass\n"
        routes.write_text(original, encoding="utf-8")
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert routes.read_text(encoding="utf-8") == original  # inchangé
        assert "register_optins(router)" in out  # branchement affiché


# ── Garde-fous périmètre ─────────────────────────────────────────────────────


class TestScopeGuards:
    def test_no_magic_discovery_in_generated_or_command(self):
        # Ni le code généré (registry) ni la commande n'utilisent de scan.
        src = ENABLE_FILE.read_text(encoding="utf-8")
        for forbidden in ("pkgutil", "iter_modules", "walk_packages"):
            assert forbidden not in src, forbidden

    def test_command_does_not_import_forge_mvc_iot(self):
        # La commande vérifie la présence via find_spec, sans **importer**
        # le paquet (Forge Core reste indépendant des opt-ins). Le seul
        # `forge_mvc_iot` du fichier est dans le contenu *généré* (string) ;
        # on vérifie via l'AST qu'aucun import réel ne le cible.
        import ast

        src = ENABLE_FILE.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("forge_mvc_iot")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("forge_mvc_iot")
        # Et la vérification de présence passe bien par find_spec.
        assert "find_spec" in src

    def test_core_does_not_import_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders

    def test_route_optins_supported(self):
        # Opt-ins routiers câblables (OPTIN-KIND-ADAPTER généralisé) : iot,
        # video et audio (forge-mvc-audio, AUDIO-MODULE-001).
        assert set(SUPPORTED_OPTINS) == {"iot", "video", "audio"}


# ── Enregistrement CLI ───────────────────────────────────────────────────────


class TestCliRegistration:
    def test_forge_py_dispatches_optin_enable(self):
        # ADR-059 : opt-in:enable est dispatchée via la table CORE_COMMANDS.
        from forge import CORE_COMMANDS

        assert "opt-in:enable" in CORE_COMMANDS

    def test_help_py_lists_optin_enable(self):
        assert "opt-in:enable" in HELP_FILE.read_text(encoding="utf-8")

    def test_help_renders(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "opt-in:enable", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "opt-in:enable" in result.stdout

    def test_forge_help_lists_optin_enable(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "opt-in:enable" in result.stdout
