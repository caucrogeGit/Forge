"""Tests administration CLI Auth/User — AUTH-ADMIN-001 et AUTH-ADMIN-002."""

from __future__ import annotations

from pathlib import Path

import pytest

import forge
from core.auth.password import verify_password
from cli.security.auth import (
    AuthAdminCliError,
    change_auth_user_password,
    cmd_auth_user_create,
    cmd_auth_user_disable,
    cmd_auth_user_enable,
    cmd_auth_user_list,
    cmd_auth_user_password,
    cmd_auth_user_show,
    create_auth_user,
    disable_auth_user,
    enable_auth_user,
    list_auth_users,
    show_auth_user,
)


def test_create_auth_user_refuse_email_vide():
    with pytest.raises(AuthAdminCliError):
        create_auth_user(email="", password="secret123", fetch_one=lambda *_: None, insert=lambda *_: 1)


def test_create_auth_user_refuse_password_vide():
    with pytest.raises(AuthAdminCliError):
        create_auth_user(email="admin@example.test", password="", fetch_one=lambda *_: None, insert=lambda *_: 1)


def test_create_auth_user_refuse_email_duplique():
    with pytest.raises(AuthAdminCliError, match="existe deja"):
        create_auth_user(
            email="admin@example.test",
            password="secret123",
            fetch_one=lambda *_: {"id": 1},
            insert=lambda *_: 2,
        )


def test_create_auth_user_hashe_le_mot_de_passe():
    captured = {}

    def fake_insert(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return 12

    user_id = create_auth_user(
        email="Admin@Example.Test",
        password="secret123",
        fetch_one=lambda *_: None,
        insert=fake_insert,
    )

    assert user_id == 12
    # La casse est CONSERVEE (`AUTH-CASE-ASYMMETRY-001`). La CLI abaissait la
    # casse quand le controleur engendre par make:auth ne le fait pas : sur
    # SQLite, qui compare en binaire, le compte devenait inaccessible depuis le
    # formulaire de connexion. Et cette colonne n'est pas une adresse, une
    # application y met legitimement `2TNE1-01`.
    assert captured["params"][0] == "Admin@Example.Test"
    password_hash = captured["params"][1]
    assert password_hash != "secret123"
    assert verify_password("secret123", password_hash) is True
    assert "password_hash" not in captured["sql"].lower().split("values", 1)[-1]


def test_cmd_create_non_interactif_ne_sort_pas_le_mot_de_passe_ni_hash(monkeypatch, capsys):
    inserted = {}

    def fake_insert(sql, params):
        inserted["hash"] = params[1]
        return 3

    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_create(
        ["--email", "admin@example.test", "--password", "secret123"],
        root=Path.cwd(),
        fetch_one=lambda *_: None,
        insert=fake_insert,
    )

    stdout = capsys.readouterr().out
    assert "Utilisateur cree" in stdout
    assert "admin@example.test" in stdout
    assert "secret123" not in stdout
    assert inserted["hash"] not in stdout


def test_cmd_create_prompt_masque(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "secret123")

    cmd_auth_user_create(
        ["--email", "admin@example.test", "--password-prompt"],
        fetch_one=lambda *_: None,
        insert=lambda *_: 4,
    )

    stdout = capsys.readouterr().out
    assert "id=4" in stdout
    assert "secret123" not in stdout


def test_cmd_create_affiche_erreur_claire_si_db_indisponible(monkeypatch):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    def broken_fetch(sql, params):
        raise AuthAdminCliError("Base de donnees Auth/User indisponible.")

    with pytest.raises(SystemExit) as exc_info:
        cmd_auth_user_create(
            ["--email", "admin@example.test", "--password", "secret123"],
            fetch_one=broken_fetch,
            insert=lambda *_: 1,
        )

    assert "Base de donnees Auth/User indisponible" in str(exc_info.value)


def test_list_auth_users_retourne_uniquement_des_champs_publics():
    users = list_auth_users(
        fetch_all=lambda *_: [
            {
                "id": 1,
                "email": "admin@example.test",
                "is_active": True,
                "created_at": "2026-01-01",
                "password_hash": "hash",
                "totp_secret": "secret",
            }
        ]
    )

    assert users == (
        {
            "id": 1,
            "email": "admin@example.test",
            "is_active": True,
            "created_at": "2026-01-01",
        },
    )


def test_cmd_user_list_naffiche_aucun_secret(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_list(
        [],
        fetch_all=lambda *_: [
            {
                "id": 1,
                "email": "admin@example.test",
                "is_active": True,
                "created_at": "2026-01-01",
                "password_hash": "hash-secret",
                "token_hash": "token-secret",
                "totp_secret": "mfa-secret",
            }
        ],
    )

    stdout = capsys.readouterr().out
    assert "admin@example.test" in stdout
    assert "password_hash" not in stdout
    assert "hash-secret" not in stdout
    assert "token-secret" not in stdout
    assert "mfa-secret" not in stdout


def test_show_auth_user_par_email():
    user = show_auth_user(
        email="Admin@Example.Test",
        fetch_one=lambda sql, params: {
            "id": 1,
            "email": params[0],
            "is_active": True,
            "created_at": "2026-01-01",
            "password_hash": "hash",
        },
    )

    assert user == {
        "id": 1,
        # Casse conservee, la recherche employant la valeur telle que saisie.
        "email": "Admin@Example.Test",
        "is_active": True,
        "created_at": "2026-01-01",
    }


def test_show_auth_user_exige_id_ou_email():
    with pytest.raises(AuthAdminCliError):
        show_auth_user(fetch_one=lambda *_: None)


def test_cmd_user_show_introuvable(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_show(["--email", "missing@example.test"], fetch_one=lambda *_: None)

    assert "Utilisateur introuvable" in capsys.readouterr().out


def test_cmd_user_show_naffiche_aucun_secret(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_show(
        ["--id", "1"],
        fetch_one=lambda *_: {
            "id": 1,
            "email": "admin@example.test",
            "is_active": True,
            "created_at": "2026-01-01",
            "password_hash": "hash-secret",
            "reset_token": "reset-secret",
        },
    )

    stdout = capsys.readouterr().out
    assert "admin@example.test" in stdout
    assert "hash-secret" not in stdout
    assert "reset-secret" not in stdout
    assert "password_hash" not in stdout


def test_dispatch_forge_auth_user_create(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:create", "--email", "a@b.test"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:create", "--email", "a@b.test"]


def test_dispatch_forge_auth_user_list(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:list"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:list"]


def test_dispatch_forge_auth_user_show(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:show", "--id", "1"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:show", "--id", "1"]


def test_auth_admin_cli_ne_depend_pas_de_librairie_externe():
    import cli.security.auth as auth_module

    source = Path(auth_module.__file__).read_text(encoding="utf-8")
    for term in ("sqlalchemy", "requests", "httpx"):
        assert term not in source


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — disable_auth_user
# ---------------------------------------------------------------------------


def _fake_fetch_by_id(user_id: int):
    def fetch(sql, params):
        if params[0] == user_id:
            return {"id": user_id}
        return None
    return fetch


def test_disable_auth_user_par_id():
    executed = {}

    def fake_exec(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    uid = disable_auth_user(
        user_id=2,
        fetch_one=_fake_fetch_by_id(2),
        execute=fake_exec,
    )

    assert uid == 2
    assert "FALSE" in executed["sql"].upper() or "false" in executed["sql"]
    assert executed["params"] == (2,)


def test_disable_auth_user_par_email():
    executed = {}

    def fake_fetch(sql, params):
        return {"id": 5}

    def fake_exec(sql, params):
        executed["params"] = params
        return 1

    uid = disable_auth_user(
        email="Admin@Example.Test",
        fetch_one=fake_fetch,
        execute=fake_exec,
    )

    assert uid == 5
    assert executed["params"] == (5,)


def test_disable_auth_user_refuse_sans_id_ni_email():
    with pytest.raises(AuthAdminCliError, match="--id ou --email"):
        disable_auth_user(fetch_one=lambda *_: None, execute=lambda *_: 1)


def test_disable_auth_user_refuse_id_et_email():
    with pytest.raises(AuthAdminCliError, match="pas les deux"):
        disable_auth_user(
            user_id=1,
            email="a@b.test",
            fetch_one=lambda *_: {"id": 1},
            execute=lambda *_: 1,
        )


def test_disable_auth_user_refuse_utilisateur_inexistant():
    with pytest.raises(AuthAdminCliError, match="introuvable"):
        disable_auth_user(
            user_id=99,
            fetch_one=lambda *_: None,
            execute=lambda *_: 1,
        )


def test_disable_auth_user_ne_supprime_pas():
    executed = {}

    def fake_exec(sql, params):
        executed["sql"] = sql
        return 1

    disable_auth_user(
        user_id=3,
        fetch_one=_fake_fetch_by_id(3),
        execute=fake_exec,
    )

    assert "DELETE" not in executed["sql"].upper()
    assert "UPDATE" in executed["sql"].upper()


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — enable_auth_user
# ---------------------------------------------------------------------------


def test_enable_auth_user_par_id():
    executed = {}

    def fake_exec(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    uid = enable_auth_user(
        user_id=7,
        fetch_one=_fake_fetch_by_id(7),
        execute=fake_exec,
    )

    assert uid == 7
    assert "TRUE" in executed["sql"].upper() or "true" in executed["sql"]
    assert executed["params"] == (7,)


def test_enable_auth_user_refuse_utilisateur_inexistant():
    with pytest.raises(AuthAdminCliError, match="introuvable"):
        enable_auth_user(
            user_id=99,
            fetch_one=lambda *_: None,
            execute=lambda *_: 1,
        )


def test_enable_ne_modifie_pas_le_mot_de_passe():
    executed = {}

    def fake_exec(sql, params):
        executed["sql"] = sql
        return 1

    enable_auth_user(
        user_id=4,
        fetch_one=_fake_fetch_by_id(4),
        execute=fake_exec,
    )

    assert "password" not in executed["sql"].lower()


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — change_auth_user_password
# ---------------------------------------------------------------------------


def test_change_password_hashe_le_nouveau_mot_de_passe():
    executed = {}

    def fake_exec(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    uid = change_auth_user_password(
        user_id=8,
        password="NouveauSecret99",
        fetch_one=_fake_fetch_by_id(8),
        execute=fake_exec,
    )

    assert uid == 8
    new_hash = executed["params"][0]
    assert new_hash != "NouveauSecret99"
    assert verify_password("NouveauSecret99", new_hash) is True


def test_change_password_remplace_ancien_hash():
    executed = {}

    def fake_exec(sql, params):
        executed["params"] = params
        return 1

    change_auth_user_password(
        user_id=1,
        password="MotDePasseA",
        fetch_one=_fake_fetch_by_id(1),
        execute=fake_exec,
    )
    first_hash = executed["params"][0]

    change_auth_user_password(
        user_id=1,
        password="MotDePasseB",
        fetch_one=_fake_fetch_by_id(1),
        execute=fake_exec,
    )
    second_hash = executed["params"][0]

    assert first_hash != second_hash
    assert verify_password("MotDePasseB", second_hash) is True
    assert verify_password("MotDePasseA", second_hash) is False


def test_change_password_refuse_mot_de_passe_vide():
    with pytest.raises(AuthAdminCliError):
        change_auth_user_password(
            user_id=1,
            password="",
            fetch_one=_fake_fetch_by_id(1),
            execute=lambda *_: 1,
        )


def test_change_password_refuse_utilisateur_inexistant():
    with pytest.raises(AuthAdminCliError, match="introuvable"):
        change_auth_user_password(
            user_id=99,
            password="secret",
            fetch_one=lambda *_: None,
            execute=lambda *_: 1,
        )


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — cmd_auth_user_disable
# ---------------------------------------------------------------------------


def test_cmd_disable_affiche_confirmation_sans_secret(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_disable(
        ["--id", "3"],
        fetch_one=_fake_fetch_by_id(3),
        execute=lambda *_: 1,
    )

    stdout = capsys.readouterr().out
    assert "desactive" in stdout
    assert "password" not in stdout.lower()
    assert "hash" not in stdout.lower()
    assert "token" not in stdout.lower()


def test_cmd_disable_erreur_db_indisponible(monkeypatch):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    def broken_fetch(sql, params):
        raise AuthAdminCliError("Base de donnees Auth/User indisponible.")

    with pytest.raises(SystemExit) as exc_info:
        cmd_auth_user_disable(
            ["--email", "a@b.test"],
            fetch_one=broken_fetch,
            execute=lambda *_: 1,
        )

    assert "indisponible" in str(exc_info.value)


def test_cmd_disable_erreur_table_absente(monkeypatch):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    def broken_fetch(sql, params):
        raise AuthAdminCliError("Table users introuvable.")

    with pytest.raises(SystemExit) as exc_info:
        cmd_auth_user_disable(
            ["--id", "1"],
            fetch_one=broken_fetch,
            execute=lambda *_: 1,
        )

    assert "users" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — cmd_auth_user_enable
# ---------------------------------------------------------------------------


def test_cmd_enable_affiche_confirmation_sans_secret(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_enable(
        ["--id", "5"],
        fetch_one=_fake_fetch_by_id(5),
        execute=lambda *_: 1,
    )

    stdout = capsys.readouterr().out
    assert "reactive" in stdout
    assert "password" not in stdout.lower()
    assert "hash" not in stdout.lower()


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — cmd_auth_user_password
# ---------------------------------------------------------------------------


def test_cmd_password_non_interactif_naffiche_pas_le_mot_de_passe(monkeypatch, capsys):
    executed = {}

    def fake_exec(sql, params):
        executed["hash"] = params[0]
        return 1

    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_password(
        ["--id", "6", "--password", "NouveauSecret99"],
        fetch_one=_fake_fetch_by_id(6),
        execute=fake_exec,
    )

    stdout = capsys.readouterr().out
    assert "NouveauSecret99" not in stdout
    assert executed["hash"] not in stdout
    assert "modifie" in stdout


def test_cmd_password_prompt_masque(monkeypatch, capsys):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "MotDePassePrompt")

    cmd_auth_user_password(
        ["--email", "a@b.test", "--password-prompt"],
        fetch_one=lambda *_: {"id": 9},
        execute=lambda *_: 1,
    )

    stdout = capsys.readouterr().out
    assert "MotDePassePrompt" not in stdout
    assert "modifie" in stdout


def test_cmd_password_refuse_mot_de_passe_vide(monkeypatch):
    monkeypatch.setattr("cli.security.auth._load_env_and_configure_forge", lambda root: None)

    with pytest.raises(SystemExit):
        cmd_auth_user_password(
            ["--id", "1", "--password", ""],
            fetch_one=_fake_fetch_by_id(1),
            execute=lambda *_: 1,
        )


# ---------------------------------------------------------------------------
# AUTH-ADMIN-002 — dispatch forge.py
# ---------------------------------------------------------------------------


def test_dispatch_forge_auth_user_disable(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:disable", "--id", "2"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:disable", "--id", "2"]


def test_dispatch_forge_auth_user_enable(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:enable", "--email", "a@b.test"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:enable", "--email", "a@b.test"]


def test_dispatch_forge_auth_user_password(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:password", "--id", "3"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:password", "--id", "3"]
