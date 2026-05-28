"""Tests de ``forge iot:init`` — IOT-INIT-COMMAND-001.

Vérifie que la commande copie la migration packagée vers
``mvc/migrations/`` du projet utilisateur, **sans appliquer** le SQL,
de façon idempotente, et avec une diagnostic clair hors projet Forge.

Aucun SQL exécuté, aucune connexion MariaDB. Les tests utilisent
``tmp_path`` pour simuler un projet Forge isolé et passent
``project_root`` explicitement à ``init_iot_migrations`` — pas de
``chdir``, pas de pollution d'état global.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from forge_mvc_iot.cli.init import (
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_OK,
    STATUS_WARN,
    init_iot_migrations,
    iter_iot_migration_resources,
    main,
)

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
HELP_FILE = PROJECT_ROOT / "forge_cli" / "help.py"
HELP_DISPATCH_FILE = PROJECT_ROOT / "forge_cli" / "help_dispatch.py"
EXPECTED_FILENAME = "20260528120000_create_iot_events.sql"
CORE_DIR = PROJECT_ROOT / "core"


# ── Helper de test ──────────────────────────────────────────────────────────


def _make_forge_project(root: Path, *, with_migrations_dir: bool = False) -> Path:
    """Crée un squelette `mvc/` minimal sous root."""
    (root / "mvc").mkdir()
    if with_migrations_dir:
        (root / "mvc" / "migrations").mkdir()
    return root


# ── Lecture des ressources ─────────────────────────────────────────────────


class TestResourcesIteration:
    def test_yields_at_least_one_sql(self):
        items = list(iter_iot_migration_resources())
        assert len(items) >= 1
        for name, content in items:
            assert name.endswith(".sql")
            assert isinstance(content, bytes)

    def test_expected_migration_present(self):
        names = {name for name, _ in iter_iot_migration_resources()}
        assert EXPECTED_FILENAME in names

    def test_content_matches_resource(self):
        items = dict(iter_iot_migration_resources())
        # On vérifie l'égalité bit-à-bit avec ce que renvoie
        # importlib.resources directement.
        anchor = resources.files("forge_mvc_iot") / "migrations"
        for name, content in items.items():
            expected = (anchor / name).read_bytes()
            assert content == expected


# ── Cas normal — copie ─────────────────────────────────────────────────────


class TestCopiesMigration:
    def test_copies_into_mvc_migrations(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        rc = init_iot_migrations(tmp_path)
        capsys.readouterr()
        assert rc == 0
        target = tmp_path / "mvc" / "migrations" / EXPECTED_FILENAME
        assert target.exists()

    def test_copied_content_matches_resource(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        init_iot_migrations(tmp_path)
        capsys.readouterr()
        target = tmp_path / "mvc" / "migrations" / EXPECTED_FILENAME
        anchor = resources.files("forge_mvc_iot") / "migrations"
        expected = (anchor / EXPECTED_FILENAME).read_bytes()
        assert target.read_bytes() == expected

    def test_creates_migrations_dir_if_missing(self, tmp_path, capsys):
        _make_forge_project(tmp_path, with_migrations_dir=False)
        assert not (tmp_path / "mvc" / "migrations").exists()
        rc = init_iot_migrations(tmp_path)
        assert rc == 0
        assert (tmp_path / "mvc" / "migrations").is_dir()
        out = capsys.readouterr().out
        assert f"{STATUS_INFO} Dossier mvc/migrations/ créé" in out

    def test_reports_copy_and_apply_hint(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        init_iot_migrations(tmp_path)
        out = capsys.readouterr().out
        assert f"{STATUS_OK} Migration IoT copiée" in out
        assert EXPECTED_FILENAME in out
        # Suggestion d'enchaînement.
        assert "forge migration:apply" in out


# ── Idempotence ─────────────────────────────────────────────────────────────


class TestIdempotence:
    def test_second_run_does_not_error(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        rc1 = init_iot_migrations(tmp_path)
        capsys.readouterr()
        rc2 = init_iot_migrations(tmp_path)
        out = capsys.readouterr().out
        assert rc1 == 0
        assert rc2 == 0
        assert f"{STATUS_OK} Migration IoT déjà présente (identique)" in out
        # La suggestion d'apply reste affichée (encore utile à l'humain).
        assert "forge migration:apply" in out

    def test_second_run_does_not_modify_file(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        init_iot_migrations(tmp_path)
        capsys.readouterr()
        target = tmp_path / "mvc" / "migrations" / EXPECTED_FILENAME
        mtime_before = target.stat().st_mtime_ns
        content_before = target.read_bytes()
        init_iot_migrations(tmp_path)
        capsys.readouterr()
        # Pas d'écrasement → contenu identique.
        assert target.read_bytes() == content_before
        # mtime aussi inchangé (pas de réécriture).
        assert target.stat().st_mtime_ns == mtime_before


# ── Pas d'écrasement silencieux ────────────────────────────────────────────


class TestNoSilentOverwrite:
    def test_existing_different_file_left_alone(self, tmp_path, capsys):
        _make_forge_project(tmp_path)
        migrations = tmp_path / "mvc" / "migrations"
        migrations.mkdir(parents=True, exist_ok=True)
        target = migrations / EXPECTED_FILENAME
        original = b"-- contenu custom de l'utilisateur\nSELECT 1;\n"
        target.write_bytes(original)

        rc = init_iot_migrations(tmp_path)
        out = capsys.readouterr().out
        assert rc == 0  # pas d'erreur fatale
        assert target.read_bytes() == original  # PAS d'écrasement
        assert f"{STATUS_WARN}" in out
        assert "existe et diffère" in out

    def test_warn_does_not_suggest_apply(self, tmp_path, capsys):
        # Quand le fichier diffère, on n'a rien copié de neuf — la
        # suggestion forge migration:apply reste pertinente seulement
        # si on a au moins une migration identique ou nouvellement
        # copiée. Ici, ni l'un ni l'autre → pas de suggestion.
        _make_forge_project(tmp_path)
        migrations = tmp_path / "mvc" / "migrations"
        migrations.mkdir(parents=True, exist_ok=True)
        (migrations / EXPECTED_FILENAME).write_bytes(b"-- different\n")

        init_iot_migrations(tmp_path)
        out = capsys.readouterr().out
        # Aucun OK identique ni copié → pas de hint apply.
        assert "forge migration:apply" not in out


# ── Pas un projet Forge ────────────────────────────────────────────────────


class TestNotAForgeProject:
    def test_returns_1_and_explains(self, tmp_path, capsys):
        # tmp_path est vide → pas de mvc/
        rc = init_iot_migrations(tmp_path)
        out = capsys.readouterr().out
        assert rc == 1
        assert f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge." in out
        assert "racine du projet" in out

    def test_no_migrations_dir_created_when_no_mvc(self, tmp_path):
        init_iot_migrations(tmp_path)
        assert not (tmp_path / "mvc").exists()
        assert not (tmp_path / "mvc" / "migrations").exists()


# ── Point d'entrée main() ──────────────────────────────────────────────────


class TestMainEntry:
    def test_main_uses_cwd_when_no_args(self, monkeypatch, tmp_path, capsys):
        _make_forge_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        rc = main([])
        capsys.readouterr()
        assert rc == 0
        assert (tmp_path / "mvc" / "migrations" / EXPECTED_FILENAME).exists()

    def test_main_returns_1_when_not_forge_project(
        self, monkeypatch, tmp_path, capsys,
    ):
        monkeypatch.chdir(tmp_path)
        rc = main(None)
        capsys.readouterr()
        assert rc == 1

    def test_main_ignores_unknown_args(self, monkeypatch, tmp_path, capsys):
        _make_forge_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        rc = main(["--unknown"])
        capsys.readouterr()
        assert rc == 0


# ── Garde-fous périmètre ───────────────────────────────────────────────────


class TestInitDoesNotTouchDb:
    """Vérifications statiques : la commande n'importe ni MariaDB ni
    core.database, ne lance aucun subscriber."""

    def test_module_does_not_import_db(self):
        from forge_mvc_iot.cli import init as init_module
        src = Path(init_module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in src.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in import_lines
            if "core.database" in line or "import mariadb" in line
        ]
        assert not offenders, (
            f"init.py ne doit pas importer la base à ce ticket : {offenders}"
        )

    def test_module_does_not_import_subscriber(self):
        from forge_mvc_iot.cli import init as init_module
        src = Path(init_module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in src.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in import_lines
            if "mqtt.subscriber" in line or "import paho" in line
        ]
        assert not offenders

    def test_module_does_not_call_migration_apply(self):
        # On ne doit pas exécuter forge migration:apply
        # automatiquement — c'est la décision de l'utilisateur.
        from forge_mvc_iot.cli import init as init_module
        src = Path(init_module.__file__).read_text(encoding="utf-8")
        assert "migration_apply" not in src
        # On peut afficher l'instruction en clair dans un print, donc
        # on tolère "forge migration:apply" comme suggestion.


class TestNoCoreImportsIot:
    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders


# ── Branchement CLI dans forge.py ──────────────────────────────────────────


class TestForgePyDispatch:
    def test_iot_init_dispatched_in_forge_py(self):
        text = FORGE_PY.read_text(encoding="utf-8")
        assert 'command == "iot:init"' in text

    def test_dispatch_uses_lazy_import_with_graceful_fallback(self):
        text = FORGE_PY.read_text(encoding="utf-8")
        # Le import est dans la branche, pas en tête de fichier.
        # Garantit que forge-mvc continue à fonctionner sans
        # forge-mvc-iot installé.
        head = text.split("def main(", 1)[0]
        assert "forge_mvc_iot.cli.init" not in head, (
            "L'import doit être paresseux : forge-mvc-iot peut ne pas "
            "être installé"
        )
        # La branche elle-même fait l'import.
        assert "from forge_mvc_iot.cli.init import" in text


class TestHelpRegistration:
    def test_help_text_lists_iot_init(self):
        text = HELP_FILE.read_text(encoding="utf-8")
        assert "iot:init" in text

    def test_help_dispatch_describes_iot_init(self):
        text = HELP_DISPATCH_FILE.read_text(encoding="utf-8")
        assert '"iot:init"' in text

    def test_rich_help_describes_iot_init(self):
        text = HELP_DISPATCH_FILE.read_text(encoding="utf-8")
        # Présence d'une entrée HELP_TEXTS_RICH.
        assert "forge iot:init" in text
        # Mention des étapes suivantes recommandées.
        assert "forge migration:apply" in text
