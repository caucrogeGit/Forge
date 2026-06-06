"""Tests MAIL-EXTRACT-001 : email deplace dans forge-mvc-mail (ADR-022)."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

_CURRENT_VERSION = tomllib.loads(
    (Path(__file__).parent.parent.parent / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["version"]
pytest.importorskip("forge_mvc_mail")

pytestmark = pytest.mark.meta


class TestMailModuleAvailable:
    def test_can_import_public_api(self):
        from forge_mvc_mail import (  # noqa: F401
            ConsoleTransport,
            MailConfig,
            MailError,
            MailMessage,
            MailTemplateRenderer,
            Mailer,
            SmtpTransport,
        )
        assert Mailer is not None

    def test_module_has_version(self):
        import forge_mvc_mail
        assert forge_mvc_mail.__version__ == _CURRENT_VERSION

    def test_cli_importable(self):
        from forge_mvc_mail.cli import main  # noqa: F401
        assert main is not None


class TestMailRemovedFromCore:
    def test_no_mail_dir_in_core(self):
        assert not Path("core/mail").exists(), "core/mail/ aurait du etre supprime"

    def test_no_mail_cli_in_forge_cli(self):
        assert not Path("forge_cli/mail.py").exists(), (
            "forge_cli/mail.py aurait du etre supprime"
        )

    def test_old_import_fails(self):
        with pytest.raises(ImportError):
            import core.mail  # noqa: F401

    def test_old_cli_import_fails(self):
        with pytest.raises(ImportError):
            import forge_cli.mail  # noqa: F401


class TestNoCoreMailImportsRemain:
    @pytest.mark.parametrize("forbidden_import", [
        "from core.mail",
        "import core.mail",
        "from forge_cli.mail import",
        "import forge_cli.mail",
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
                if forbidden_import in py_file.read_text(encoding="utf-8"):
                    offenders.append(str(py_file))
        assert not offenders, (
            f"References a l'ancien chemin mail restantes dans : {offenders}"
        )


class TestMailFunctional:
    def test_send_via_fake_transport(self):
        from forge_mvc_mail import FakeTransport, Mailer, MailMessage

        transport = FakeTransport()
        mailer = Mailer(transport)
        mailer.send(MailMessage(
            subject="Bonjour",
            to="dest@example.com",
            body_text="Contenu de test.",
        ))
        assert transport.sent_count == 1


class TestPyprojectMetadata:
    def test_pyproject_version(self):
        content = Path("packages/forge-mvc-mail/pyproject.toml").read_text(encoding="utf-8")
        assert f'version = "{_CURRENT_VERSION}"' in content

    def test_forge_mvc_dependency_declared(self):
        content = Path("packages/forge-mvc-mail/pyproject.toml").read_text(encoding="utf-8")
        assert "forge-mvc>=" in content
