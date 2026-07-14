"""Tests — opt-in:enable, câblage de routes en affichage seul (ADR-085).

`forge opt-in:enable <nom>` n'écrit JAMAIS dans `mvc/routes/__init__.py`
(ADR-085, révise OPTINS-CLI-ENABLE-ROUTES-APPLY-001) : le branchement
`register_optins(router)` est **affiché** à coller à la main, jamais injecté,
même en `--apply`. Vérifie :

- routes/__init__.py n'est jamais modifié (dry-run comme --apply) ;
- le branchement (import + appel) est affiché ;
- si l'appel est déjà présent → `[OK] déjà branché`, aucune écriture ;
- routes/__init__.py absent → branchement affiché quand même ;
- conflit `optins/` existant → toujours bloquant (comportement conservé) ;
- pas de discovery magique ; `core/` n'importe pas les opt-ins.
"""

from __future__ import annotations

from pathlib import Path

from cli.optins.enable import enable_optin

_REPO_ROOT = Path(__file__).resolve().parent.parent
ENABLE_FILE = _REPO_ROOT / "cli" / "optins" / "enable.py"
CORE_DIR = _REPO_ROOT / "core"

_PKG_OK = lambda _name: True  # noqa: E731

_ROUTES = (
    "from core.http.router import Router\n"
    "\n"
    "router = Router()\n"
)

_IMPORT = "from optins.registry import register_optins"
_CALL = "register_optins(router)"


def _write_routes(tmp_path: Path, content: str) -> Path:
    mvc = tmp_path / "mvc"
    (mvc / "routes").mkdir(parents=True, exist_ok=True)
    routes = mvc / "routes" / "__init__.py"
    routes.write_text(content, encoding="utf-8")
    return routes


# ── routes/__init__.py n'est JAMAIS modifié (ADR-085) ────────────────────────


class TestRoutesNeverWritten:
    def test_dry_run_affiche_le_branchement_sans_ecrire(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _ROUTES)
        rc = enable_optin("iot", project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert routes.read_text(encoding="utf-8") == _ROUTES  # inchangé
        assert _IMPORT in out and _CALL in out
        assert "Branchement à ajouter" in out

    def test_apply_n_injecte_pas(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _ROUTES)
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        # Le changement clé : --apply n'écrit PLUS dans routes/__init__.py.
        assert routes.read_text(encoding="utf-8") == _ROUTES
        assert _IMPORT in out and _CALL in out


# ── Déjà branché : signalé, rien à faire ─────────────────────────────────────


class TestAlreadyBranched:
    def test_appel_present_signale_deja_branche(self, tmp_path, capsys):
        content = _ROUTES + f"\n{_IMPORT}\n\n{_CALL}\n"
        routes = _write_routes(tmp_path, content)
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert routes.read_text(encoding="utf-8") == content  # inchangé
        assert "déjà branché" in out


# ── routes/__init__.py absent : branchement affiché quand même ───────────────


class TestMissingRoutes:
    def test_absent_affiche_le_branchement(self, tmp_path, capsys):
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert not (tmp_path / "mvc" / "routes" / "__init__.py").exists()
        assert _CALL in out
        assert rc == 0


# ── Conflit optins/ : comportement existant conservé ─────────────────────────


class TestOptinsConflictStillBlocks:
    def test_divergent_optins_file_blocks(self, tmp_path, capsys):
        _write_routes(tmp_path, _ROUTES)
        reg = tmp_path / "optins" / "registry.py"
        reg.parent.mkdir(parents=True)
        reg.write_text("# custom registry\n", encoding="utf-8")

        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        capsys.readouterr()
        assert rc == 1  # conflit optins/ → exit 1 (conservé)


# ── Garde-fous périmètre ─────────────────────────────────────────────────────


class TestScopeGuards:
    def test_ne_reecrit_jamais_routes_init(self):
        # ADR-085 : plus aucune écriture dans routes/__init__.py.
        src = ENABLE_FILE.read_text(encoding="utf-8")
        assert "routes_path.write_text" not in src, (
            "opt-in:enable ne doit plus écrire dans mvc/routes/__init__.py (ADR-085)."
        )

    def test_no_magic_discovery(self):
        src = ENABLE_FILE.read_text(encoding="utf-8")
        for forbidden in ("pkgutil", "iter_modules", "walk_packages"):
            assert forbidden not in src, forbidden

    def test_core_does_not_import_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders
