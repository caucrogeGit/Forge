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
    captured = {}

    def fake_upload_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "upload:init"])
    monkeypatch.setattr(forge, "upload_main", fake_upload_main)

    forge.main()

    assert captured["args"] == ["upload:init"]
