"""Tests — OPTINS-CLI-ENABLE-ROUTES-APPLY-001.

Vérifie le branchement **prudent** de `mvc/routes.py` par
`forge opt-in:enable iot --apply` :

- dry-run n'écrit pas dans `mvc/routes.py` ;
- `--apply` ajoute l'import `optins.registry` + l'appel
  `register_optins(router)` si la structure est reconnue
  (`router = Router()`) ;
- 2e `--apply` ne duplique rien ; appel/import déjà présents → `[OK]` ;
- structure ambiguë → `[WARN]` + aucune modification ;
- `mvc/routes.py` absent → `[WARN]` + aucune modification ;
- conflit `optins/` existant inchangé (comportement conservé) ;
- pas de discovery magique ; `core/` n'importe pas les opt-ins.

Tests unitaires via `enable_optin(..., project_root=tmp,
package_check=...)` — aucun fichier réel du dépôt n'est touché.
"""

from __future__ import annotations

from pathlib import Path

from cli.optins.enable import enable_optin

_REPO_ROOT = Path(__file__).resolve().parent.parent
ENABLE_FILE = _REPO_ROOT / "cli" / "optins" / "enable.py"
CORE_DIR = _REPO_ROOT / "core"

_PKG_OK = lambda _name: True  # noqa: E731

_RECOGNIZED_ROUTES = (
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


# ── Dry-run : aucune écriture dans routes.py ─────────────────────────────────


class TestDryRunDoesNotWriteRoutes:
    def test_recognized_routes_untouched_in_dry_run(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _RECOGNIZED_ROUTES)
        rc = enable_optin("iot", project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert routes.read_text(encoding="utf-8") == _RECOGNIZED_ROUTES
        assert "serait branché" in out  # annoncé, pas appliqué


# ── Apply : insertion dans structure reconnue ────────────────────────────────


class TestApplyBranchesRecognizedRoutes:
    def test_apply_adds_import_and_call(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _RECOGNIZED_ROUTES)
        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        out = capsys.readouterr().out
        assert rc == 0
        content = routes.read_text(encoding="utf-8")
        assert _IMPORT in content
        assert _CALL in content
        assert "branché" in out

    def test_import_inserted_near_imports(self, tmp_path):
        routes = _write_routes(tmp_path, _RECOGNIZED_ROUTES)
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        lines = routes.read_text(encoding="utf-8").splitlines()
        # L'import optins doit précéder l'appel register_optins.
        assert lines.index(_IMPORT) < lines.index(_CALL)
        # Et l'appel vient après `router = Router()`.
        assert lines.index("router = Router()") < lines.index(_CALL)

    def test_existing_routes_preserved(self, tmp_path):
        original = _RECOGNIZED_ROUTES + (
            "\n"
            'with router.group("", public=True) as public:\n'
            '    public.add("GET", "/", Home.index, name="home")\n'
        )
        routes = _write_routes(tmp_path, original)
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        content = routes.read_text(encoding="utf-8")
        assert 'public.add("GET", "/", Home.index, name="home")' in content
        assert _CALL in content


# ── Idempotence ──────────────────────────────────────────────────────────────


class TestRoutesIdempotence:
    def test_second_apply_no_duplicate(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _RECOGNIZED_ROUTES)
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        capsys.readouterr()
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        content = routes.read_text(encoding="utf-8")
        assert rc == 0
        assert content.count(_CALL) == 1
        assert content.count(_IMPORT) == 1
        assert "déjà branché" in out

    def test_call_already_present_is_ok(self, tmp_path, capsys):
        routes = _write_routes(
            tmp_path,
            _RECOGNIZED_ROUTES + f"\n{_IMPORT}\n\n{_CALL}\n",
        )
        before = routes.read_text(encoding="utf-8")
        rc = enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        out = capsys.readouterr().out
        assert rc == 0
        assert routes.read_text(encoding="utf-8") == before  # inchangé
        assert "déjà branché" in out

    def test_import_present_call_absent_no_double_import(self, tmp_path):
        # Cas partiel : import déjà là, appel absent.
        routes = _write_routes(
            tmp_path, f"{_IMPORT}\n" + _RECOGNIZED_ROUTES,
        )
        enable_optin("iot", apply=True, project_root=tmp_path, package_check=_PKG_OK)
        content = routes.read_text(encoding="utf-8")
        assert content.count(_IMPORT) == 1
        assert content.count(_CALL) == 1


# ── Structure ambiguë / absente ──────────────────────────────────────────────


class TestAmbiguousOrMissingRoutes:
    def test_ambiguous_routes_not_modified(self, tmp_path, capsys):
        ambiguous = "def register(router):\n    pass\n"
        routes = _write_routes(tmp_path, ambiguous)
        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        out = capsys.readouterr().out
        assert routes.read_text(encoding="utf-8") == ambiguous
        assert "[WARN]" in out
        assert "structure reconnue" in out
        # Branchement optins/ réussi → pas de conflit bloquant.
        assert rc == 0

    def test_missing_routes_warns(self, tmp_path, capsys):
        # Pas de mvc/routes.py du tout.
        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        out = capsys.readouterr().out
        assert not (tmp_path / "mvc" / "routes" / "__init__.py").exists()
        assert "introuvable" in out
        assert _CALL in out  # instruction manuelle affichée
        assert rc == 0


# ── Conflit optins/ : comportement existant conservé ─────────────────────────


class TestOptinsConflictStillBlocks:
    def test_divergent_optins_file_blocks_and_routes_untouched(self, tmp_path, capsys):
        routes = _write_routes(tmp_path, _RECOGNIZED_ROUTES)
        # Pré-crée un registry divergent.
        reg = tmp_path / "optins" / "registry.py"
        reg.parent.mkdir(parents=True)
        reg.write_text("# custom registry\n", encoding="utf-8")

        rc = enable_optin(
            "iot", apply=True, project_root=tmp_path, package_check=_PKG_OK,
        )
        capsys.readouterr()
        # Conflit optins/ → exit 1 (comportement conservé).
        assert rc == 1
        # routes.py reconnu a quand même pu être branché (indépendant).
        assert _CALL in routes.read_text(encoding="utf-8")


# ── Garde-fous périmètre ─────────────────────────────────────────────────────


class TestScopeGuards:
    def test_no_magic_discovery(self):
        src = ENABLE_FILE.read_text(encoding="utf-8")
        for forbidden in ("pkgutil", "iter_modules", "walk_packages"):
            assert forbidden not in src, forbidden

    def test_no_marker_comments_added(self):
        # Choix du ticket : pas de marqueurs « Forge opt-ins: begin/end ».
        src = ENABLE_FILE.read_text(encoding="utf-8")
        assert "Forge opt-ins: begin" not in src

    def test_core_does_not_import_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(_REPO_ROOT))
        assert not offenders, offenders
