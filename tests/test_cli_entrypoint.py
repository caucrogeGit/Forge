"""Tests de cli_entrypoint — gestion de Ctrl+C dans la CLI Forge."""

import sys
import pytest
import forge


def test_keyboard_interrupt_exit_code(monkeypatch):
    monkeypatch.setattr(forge, "main", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit) as exc_info:
        forge.cli_entrypoint()
    assert exc_info.value.code == 130


def test_keyboard_interrupt_message_sur_stderr(monkeypatch, capsys):
    monkeypatch.setattr(forge, "main", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        forge.cli_entrypoint()
    captured = capsys.readouterr()
    assert "Interruption utilisateur. Commande annulée." in captured.err
    assert captured.out == ""


def test_keyboard_interrupt_pas_de_traceback(monkeypatch, capsys):
    monkeypatch.setattr(forge, "main", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit):
        forge.cli_entrypoint()
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "KeyboardInterrupt" not in captured.err


def test_autres_exceptions_non_masquees(monkeypatch):
    monkeypatch.setattr(forge, "main", lambda: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        forge.cli_entrypoint()


def test_succes_nominal(monkeypatch):
    monkeypatch.setattr(forge, "main", lambda: None)
    forge.cli_entrypoint()  # ne doit pas lever


def test_dispatch_build_model_transmet_dry_run(monkeypatch):
    captured = {}

    def fake_model_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "build:model", "--dry-run"])
    monkeypatch.setattr(forge, "model_main", fake_model_main)

    forge.main()

    assert captured["args"] == ["build:model", "--dry-run"]


def test_dispatch_build_model_sans_dry_run(monkeypatch):
    captured = {}

    def fake_model_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "build:model"])
    monkeypatch.setattr(forge, "model_main", fake_model_main)

    forge.main()

    assert captured["args"] == ["build:model"]


def test_dispatch_sync_landing_transmet_check(monkeypatch):
    captured = {}

    def fake_sync_landing_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "sync:landing", "--check"])
    monkeypatch.setattr(forge, "sync_landing_main", fake_sync_landing_main)

    forge.main()

    assert captured["args"] == ["sync:landing", "--check"]


def test_dispatch_upload_init(monkeypatch):
    # FILES-CLI-RENAME-001 (ADR-019) : cli.uploads est importé en lazy
    # dans la branche (l'upload est un opt-in). On patche la vraie cible.
    import cli.uploads as _uploads

    captured = {}

    def fake_upload_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "upload:init"])
    monkeypatch.setattr(_uploads, "main", fake_upload_main)

    forge.main()

    assert captured["args"] == ["upload:init"]


def test_dispatch_js_init_htmx(monkeypatch):
    captured = {}

    def fake_front_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "js:init", "htmx"])
    monkeypatch.setattr(forge, "front_main", fake_front_main)

    forge.main()

    assert captured["args"] == ["js:init", "htmx"]


def test_dispatch_make_public_page(monkeypatch):
    captured = {}

    def fake_public_page_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "make:public-page", "accueil"])
    monkeypatch.setattr(forge, "public_page_main", fake_public_page_main)

    forge.main()

    assert captured["args"] == ["accueil"]


def test_dispatch_make_public_list(monkeypatch):
    captured = {}

    def fake_public_list_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "make:public-list", "Hebergement"])
    monkeypatch.setattr(forge, "public_list_main", fake_public_list_main)

    forge.main()

    assert captured["args"] == ["Hebergement"]


def test_dispatch_make_public_show(monkeypatch):
    captured = {}

    def fake_public_show_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "make:public-show", "Hebergement"])
    monkeypatch.setattr(forge, "public_show_main", fake_public_show_main)

    forge.main()

    assert captured["args"] == ["Hebergement"]


def test_dispatch_make_public_contact(monkeypatch):
    captured = {}

    def fake_public_contact_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "make:public-contact"])
    monkeypatch.setattr(forge, "public_contact_main", fake_public_contact_main)

    forge.main()

    assert captured["args"] == []


def test_dispatch_make_public_form(monkeypatch):
    captured = {}

    def fake_public_form_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "make:public-form", "Demande"])
    monkeypatch.setattr(forge, "public_form_main", fake_public_form_main)

    forge.main()

    assert captured["args"] == ["Demande"]


def test_dispatch_js_init_alpine(monkeypatch):
    captured = {}

    def fake_front_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "js:init", "alpine"])
    monkeypatch.setattr(forge, "front_main", fake_front_main)

    forge.main()

    assert captured["args"] == ["js:init", "alpine"]


def test_dispatch_js_init_htmx_alpine(monkeypatch):
    captured = {}

    def fake_front_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "js:init", "htmx-alpine"])
    monkeypatch.setattr(forge, "front_main", fake_front_main)

    forge.main()

    assert captured["args"] == ["js:init", "htmx-alpine"]


def test_dispatch_migration_status(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "migration:status"])
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:status"]


def test_dispatch_migration_apply(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "migration:apply"])
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:apply"]


def test_dispatch_migration_make(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "migration:make", "create_contacts"])
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:make", "create_contacts"]


def test_dispatch_migration_make_from_entity(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "migration:make", "create_contacts", "--from-entity", "Contact"],
    )
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:make", "create_contacts", "--from-entity", "Contact"]


def test_dispatch_migration_make_from_entities(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "migration:make", "initial_schema", "--from-entities"],
    )
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:make", "initial_schema", "--from-entities"]


def test_dispatch_migration_make_from_diff(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "migration:make", "add_contact_fields", "--from-diff", "Contact"],
    )
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == [
        "migration:make",
        "add_contact_fields",
        "--from-diff",
        "Contact",
    ]


def test_dispatch_migration_diff_entity(monkeypatch):
    captured = {}

    def fake_migrations_main(args):
        captured["args"] = args

    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "migration:diff", "--entity", "Contact"],
    )
    monkeypatch.setattr(forge, "migrations_main", fake_migrations_main)

    forge.main()

    assert captured["args"] == ["migration:diff", "--entity", "Contact"]
