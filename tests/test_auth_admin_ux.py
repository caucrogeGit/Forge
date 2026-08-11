"""Tests — AUTH-ADMIN-UX-001 : clarté et harmonisation de l'administration utilisateur.

Vérifie que :
- les erreurs CLI suivent la convention Erreur: / Conseil: ;
- les commandes disable/enable/password sont claires et cohérentes ;
- aucun secret n'est jamais affiché ;
- les événements d'audit sont définis et logguables ;
- la documentation est présente.
"""
from __future__ import annotations

import pathlib

import pytest

from cli.security.auth import (
    AuthAdminCliError,
    cmd_auth_user_disable,
    cmd_auth_user_enable,
    cmd_auth_user_password,
)


# ---------------------------------------------------------------------------
# Helpers communs
# ---------------------------------------------------------------------------

def _patch_env(monkeypatch):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)


def _fake_fetch_by_id(uid: int):
    def fetch(sql, params):
        if "WHERE id = ?" in sql and params == (uid,):
            return {"id": uid}
        return None
    return fetch


def _fake_fetch_by_login(login: str, uid: int = 42):
    """La CLI designe un compte par son IDENTITE, donc par `WHERE login = ?`."""
    def fetch(sql, params):
        if "WHERE login = ?" in sql and params == (login,):
            return {"id": uid}
        return None
    return fetch


def _fake_fetch_role(role_id: int = 10):
    def fetch(sql, params):
        if "roles" in sql:
            return {"id": role_id}
        return {"id": 1}
    return fetch


# ---------------------------------------------------------------------------
# Convention Erreur: / Conseil:
# ---------------------------------------------------------------------------

class TestConventionErreurConseil:
    def test_erreur_sans_identifiant_contient_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable([], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "Erreur :" in str(exc.value)

    def test_erreur_sans_identifiant_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable([], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "Conseil :" in str(exc.value)

    def test_erreur_double_identifiant_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(
                ["--id", "1", "--login", "a@b.test"],
                fetch_one=_fake_fetch_by_id(1),
                execute=lambda *_: 1,
            )
        assert "Conseil :" in str(exc.value)

    def test_erreur_user_introuvable_par_id_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(
                ["--id", "999"],
                fetch_one=lambda *_: None,
                execute=lambda *_: 1,
            )
        assert "Conseil :" in str(exc.value)

    def test_erreur_user_introuvable_par_email_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(
                ["--login", "inconnu@test.com"],
                fetch_one=lambda *_: None,
                execute=lambda *_: 1,
            )
        assert "Conseil :" in str(exc.value)

    def test_erreur_contact_invalide_contient_conseil(self):
        """Le controle de forme vit desormais sur le CONTACT (ADR-089).

        Sur l'identite il n'avait aucun sens et refusait la saisie avant meme
        de chercher le compte : `2TNE1-01` etait rejete, pas cherche.
        """
        with pytest.raises(AuthAdminCliError) as exc:
            from cli.security.auth import _validate_contact_value
            _validate_contact_value("pasdetat")
        assert exc.value.conseil

    def test_une_identite_sans_arobase_est_acceptee(self):
        """C'est le point du ticket : `2TNE1-01` est une identite valide."""
        from cli.security.auth import _validate_login_value

        assert _validate_login_value("2TNE1-01") == "2TNE1-01"

    def test_erreur_email_vide_contient_conseil(self):
        with pytest.raises(AuthAdminCliError) as exc:
            from cli.security.auth import _validate_login_value
            _validate_login_value("")
        assert exc.value.conseil

    def test_erreur_mot_de_passe_vide_contient_conseil(self):
        with pytest.raises(AuthAdminCliError) as exc:
            from cli.security.auth import _validate_password_value
            _validate_password_value("")
        assert exc.value.conseil

    def test_erreur_id_negatif_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(
                ["--id", "-1"],
                fetch_one=lambda *_: None,
                execute=lambda *_: 1,
            )
        assert "Conseil :" in str(exc.value)

    def test_db_indisponible_contient_conseil(self, monkeypatch):
        _patch_env(monkeypatch)

        def broken(sql, params):
            raise AuthAdminCliError("Base de donnees Auth/User indisponible.", conseil="Verifiez env/dev.")

        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(["--login", "a@b.test"], fetch_one=broken, execute=lambda *_: 1)
        assert "Conseil :" in str(exc.value)


# ---------------------------------------------------------------------------
# disable par login et par id
# ---------------------------------------------------------------------------

class TestDisable:
    def test_disable_par_login_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_disable(
            ["--login", "user@example.com"],
            fetch_one=_fake_fetch_by_login("user@example.com", uid=7),
            execute=lambda *_: 1,
        )
        assert "desactive" in capsys.readouterr().out

    def test_disable_par_id_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_disable(
            ["--id", "7"],
            fetch_one=_fake_fetch_by_id(7),
            execute=lambda *_: 1,
        )
        assert "desactive" in capsys.readouterr().out

    def test_disable_affiche_id_utilisateur(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_disable(
            ["--id", "7"],
            fetch_one=_fake_fetch_by_id(7),
            execute=lambda *_: 1,
        )
        out = capsys.readouterr().out
        assert "id=7" in out

    def test_disable_user_introuvable_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(["--id", "999"], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "introuvable" in str(exc.value)

    def test_disable_sans_argument_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable([], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "Erreur :" in str(exc.value)

    def test_disable_double_arg_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_disable(
                ["--id", "1", "--login", "a@b.test"],
                fetch_one=_fake_fetch_by_id(1),
                execute=lambda *_: 1,
            )
        assert "Erreur :" in str(exc.value)

    def test_disable_ne_revele_pas_de_secret(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_disable(
            ["--id", "7"],
            fetch_one=_fake_fetch_by_id(7),
            execute=lambda *_: 1,
        )
        out = capsys.readouterr().out
        for mot in ("password", "hash", "token", "secret"):
            assert mot not in out.lower()


# ---------------------------------------------------------------------------
# enable par email et par id
# ---------------------------------------------------------------------------

class TestEnable:
    def test_enable_par_login_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_enable(
            ["--login", "user@example.com"],
            fetch_one=_fake_fetch_by_login("user@example.com", uid=8),
            execute=lambda *_: 1,
        )
        assert "reactive" in capsys.readouterr().out

    def test_enable_par_id_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_enable(
            ["--id", "8"],
            fetch_one=_fake_fetch_by_id(8),
            execute=lambda *_: 1,
        )
        assert "reactive" in capsys.readouterr().out

    def test_enable_affiche_id_utilisateur(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_enable(
            ["--id", "8"],
            fetch_one=_fake_fetch_by_id(8),
            execute=lambda *_: 1,
        )
        assert "id=8" in capsys.readouterr().out

    def test_enable_user_introuvable_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_enable(["--id", "999"], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "introuvable" in str(exc.value)

    def test_enable_sans_argument_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_enable([], fetch_one=lambda *_: None, execute=lambda *_: 1)
        assert "Erreur :" in str(exc.value)

    def test_enable_ne_revele_pas_de_secret(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_enable(
            ["--id", "8"],
            fetch_one=_fake_fetch_by_id(8),
            execute=lambda *_: 1,
        )
        out = capsys.readouterr().out
        for mot in ("password", "hash", "token", "secret"):
            assert mot not in out.lower()


# ---------------------------------------------------------------------------
# password par email et par id
# ---------------------------------------------------------------------------

class TestPassword:
    def test_password_par_id_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_password(
            ["--id", "9", "--password", "nouveauSecret99"],
            fetch_one=_fake_fetch_by_id(9),
            execute=lambda *_: 1,
        )
        assert "modifie" in capsys.readouterr().out

    def test_password_par_email_affiche_confirmation(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_password(
            ["--login", "user@example.com", "--password", "nouveauSecret99"],
            fetch_one=_fake_fetch_by_login("user@example.com", uid=9),
            execute=lambda *_: 1,
        )
        assert "modifie" in capsys.readouterr().out

    def test_password_ne_revele_pas_le_mot_de_passe(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_password(
            ["--id", "9", "--password", "secretNePasAfficher"],
            fetch_one=_fake_fetch_by_id(9),
            execute=lambda *_: 1,
        )
        out = capsys.readouterr().out
        assert "secretNePasAfficher" not in out
        assert "password_hash" not in out.lower()

    def test_password_mot_de_passe_vide_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_password(
                ["--id", "9", "--password", ""],
                fetch_one=_fake_fetch_by_id(9),
                execute=lambda *_: 1,
            )
        assert "Erreur :" in str(exc.value)

    def test_password_mot_de_passe_vide_conseil(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_password(
                ["--id", "9", "--password", ""],
                fetch_one=_fake_fetch_by_id(9),
                execute=lambda *_: 1,
            )
        assert "Conseil :" in str(exc.value)

    def test_password_user_introuvable_erreur(self, monkeypatch):
        _patch_env(monkeypatch)
        with pytest.raises(SystemExit) as exc:
            cmd_auth_user_password(
                ["--id", "999", "--password", "ok"],
                fetch_one=lambda *_: None,
                execute=lambda *_: 1,
            )
        assert "introuvable" in str(exc.value)

    def test_password_affiche_id_utilisateur(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_password(
            ["--id", "9", "--password", "monSecret"],
            fetch_one=_fake_fetch_by_id(9),
            execute=lambda *_: 1,
        )
        assert "id=9" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Événements d'audit — constantes et logguabilité
# ---------------------------------------------------------------------------

class TestEvenementsAudit:
    def test_event_user_disabled_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_DISABLED
        assert AUTH_EVENT_USER_DISABLED == "user.disabled"

    def test_event_user_enabled_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_ENABLED
        assert AUTH_EVENT_USER_ENABLED == "user.enabled"

    def test_event_user_password_changed_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_PASSWORD_CHANGED
        assert AUTH_EVENT_USER_PASSWORD_CHANGED == "user.password_changed"

    def test_event_user_not_found_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_NOT_FOUND
        assert AUTH_EVENT_USER_NOT_FOUND == "user.not_found"

    def test_event_user_role_added_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_ROLE_ADDED
        assert AUTH_EVENT_USER_ROLE_ADDED == "user_role.added"

    def test_event_user_role_removed_defini(self):
        from core.auth.audit import AUTH_EVENT_USER_ROLE_REMOVED
        assert AUTH_EVENT_USER_ROLE_REMOVED == "user_role.removed"

    def test_events_dans_auth_audit_event_types(self):
        from core.auth.audit import AUTH_AUDIT_EVENT_TYPES
        for event in (
            "user.disabled",
            "user.enabled",
            "user.password_changed",
            "user.not_found",
            "user_role.added",
            "user_role.removed",
        ):
            assert event in AUTH_AUDIT_EVENT_TYPES, f"{event!r} absent de AUTH_AUDIT_EVENT_TYPES"

    def test_events_exportes_depuis_core_auth(self):
        import core.auth
        for name in (
            "AUTH_EVENT_USER_DISABLED",
            "AUTH_EVENT_USER_ENABLED",
            "AUTH_EVENT_USER_PASSWORD_CHANGED",
            "AUTH_EVENT_USER_NOT_FOUND",
            "AUTH_EVENT_USER_ROLE_ADDED",
            "AUTH_EVENT_USER_ROLE_REMOVED",
        ):
            assert hasattr(core.auth, name), f"{name} non exporté depuis core.auth"

    def test_log_auth_event_appel_nominal_user_disabled(self):
        from core.auth.audit import AUTH_EVENT_USER_DISABLED, log_auth_event
        log_auth_event(AUTH_EVENT_USER_DISABLED, user_id=1)

    def test_log_auth_event_appel_nominal_user_not_found(self):
        from core.auth.audit import AUTH_EVENT_USER_NOT_FOUND, log_auth_event
        log_auth_event(AUTH_EVENT_USER_NOT_FOUND, metadata={"attempted_id": 999})

    def test_cli_disable_appelle_audit_event(self, monkeypatch, capsys):
        called = []
        monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

        def fake_log(event_type, **kwargs):
            called.append(event_type)

        monkeypatch.setattr(
            "core.auth.audit.log_auth_event",
            fake_log,
        )
        cmd_auth_user_disable(
            ["--id", "1"],
            fetch_one=_fake_fetch_by_id(1),
            execute=lambda *_: 1,
        )
        assert "user.disabled" in called

    def test_cli_enable_appelle_audit_event(self, monkeypatch, capsys):
        called = []
        monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)
        monkeypatch.setattr("core.auth.audit.log_auth_event", lambda event, **kw: called.append(event))
        cmd_auth_user_enable(
            ["--id", "2"],
            fetch_one=_fake_fetch_by_id(2),
            execute=lambda *_: 1,
        )
        assert "user.enabled" in called

    def test_cli_password_appelle_audit_event(self, monkeypatch, capsys):
        called = []
        monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)
        monkeypatch.setattr("core.auth.audit.log_auth_event", lambda event, **kw: called.append(event))
        cmd_auth_user_password(
            ["--id", "3", "--password", "nouveauMdp99"],
            fetch_one=_fake_fetch_by_id(3),
            execute=lambda *_: 1,
        )
        assert "user.password_changed" in called

    def test_audit_ne_logue_pas_le_mot_de_passe(self, monkeypatch):
        logged_meta = {}
        monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

        def capture_log(event, **kwargs):
            logged_meta.update(kwargs)

        monkeypatch.setattr("core.auth.audit.log_auth_event", capture_log)
        cmd_auth_user_password(
            ["--id", "3", "--password", "secretNePasLogger"],
            fetch_one=_fake_fetch_by_id(3),
            execute=lambda *_: 1,
        )
        for key, val in logged_meta.items():
            if isinstance(val, str):
                assert "secretNePasLogger" not in val
            if isinstance(val, dict):
                for k, v in val.items():
                    assert k not in ("password", "password_hash", "token", "secret")


# ---------------------------------------------------------------------------
# Aucun secret dans aucune sortie
# ---------------------------------------------------------------------------

class TestAucunSecretEnSortie:
    def test_disable_aucun_hash(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_disable(["--id", "1"], fetch_one=_fake_fetch_by_id(1), execute=lambda *_: 1)
        assert "hash" not in capsys.readouterr().out.lower()

    def test_enable_aucun_hash(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_enable(["--id", "1"], fetch_one=_fake_fetch_by_id(1), execute=lambda *_: 1)
        assert "hash" not in capsys.readouterr().out.lower()

    def test_password_aucun_hash_en_clair(self, monkeypatch, capsys):
        _patch_env(monkeypatch)
        cmd_auth_user_password(
            ["--id", "1", "--password", "testSecret"],
            fetch_one=_fake_fetch_by_id(1),
            execute=lambda *_: 1,
        )
        out = capsys.readouterr().out
        assert "testSecret" not in out
        assert "password_hash" not in out


# ---------------------------------------------------------------------------
# Documentation — sections présentes
# ---------------------------------------------------------------------------

class TestDocumentation:
    _auth_md = pathlib.Path("docs/features/auth.md").read_text(encoding="utf-8")
    # Référence CLI : catalogue concis listant les commandes (DOCS-CLI-COMMANDS-CATALOG-001).
    _ref_md = pathlib.Path("docs/reference/cli-commands.md").read_text(encoding="utf-8")

    def test_auth_md_contient_disable(self):
        assert "auth:user:disable" in self._auth_md

    def test_auth_md_contient_enable(self):
        assert "auth:user:enable" in self._auth_md

    def test_auth_md_contient_password(self):
        assert "auth:user:password" in self._auth_md

    def test_auth_md_contient_erreur_conseil(self):
        assert ("Conseil" in self._auth_md or "conseil" in self._auth_md)

    def test_auth_md_contient_audit_admin(self):
        assert "user.disabled" in self._auth_md or "user.enabled" in self._auth_md

    def test_reference_md_contient_disable(self):
        assert "auth:user:disable" in self._ref_md

    def test_reference_md_contient_enable(self):
        assert "auth:user:enable" in self._ref_md

    def test_reference_md_contient_password(self):
        assert "auth:user:password" in self._ref_md
