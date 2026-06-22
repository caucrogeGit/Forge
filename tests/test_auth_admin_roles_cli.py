"""Tests AUTH-ADMIN-ROLE-CLI-001 — commandes CLI roles utilisateur."""

from __future__ import annotations

from pathlib import Path

import pytest

import forge
from cli.auth import (
    AuthAdminCliError,
    add_auth_user_role,
    cmd_auth_user_role_add,
    cmd_auth_user_role_remove,
    cmd_auth_user_roles,
    list_auth_user_roles,
    remove_auth_user_role,
)


def _fetch_for_roles(*, user=None, role=None, association=None):
    def fetch(sql, params):
        normalized = " ".join(sql.lower().split())
        if "from users" in normalized:
            return user
        if "from roles" in normalized:
            return role
        if "from user_roles" in normalized:
            return association
        return None

    return fetch


def test_dispatch_forge_auth_user_role_add(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:role:add", "--id", "1", "--role", "admin"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:role:add", "--id", "1", "--role", "admin"]


def test_dispatch_forge_auth_user_role_remove(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:role:remove", "--id", "1", "--role", "admin"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:role:remove", "--id", "1", "--role", "admin"]


def test_dispatch_forge_auth_user_roles(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:user:roles", "--id", "1"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:user:roles", "--id", "1"]


def test_add_resout_utilisateur_par_id():
    seen = []

    def fetch(sql, params):
        seen.append((sql, params))
        return _fetch_for_roles(user={"id": 7}, role={"id": 2})(sql, params)

    add_auth_user_role(user_id=7, role="admin", fetch_one=fetch, execute=lambda *_: 1)

    assert any("FROM users WHERE id" in sql for sql, _ in seen)
    assert any(params == (7,) for _, params in seen)


def test_add_resout_utilisateur_par_email():
    seen = []

    def fetch(sql, params):
        seen.append((sql, params))
        return _fetch_for_roles(user={"id": 7}, role={"id": 2})(sql, params)

    result = add_auth_user_role(
        email="Admin@Example.Test",
        role="admin",
        fetch_one=fetch,
        execute=lambda *_: 1,
    )

    assert result["user_id"] == 7
    assert any(params == ("admin@example.test",) for _, params in seen)


def test_add_resout_role_par_id():
    seen = []

    def fetch(sql, params):
        seen.append((sql, params))
        return _fetch_for_roles(user={"id": 7}, role={"id": 2})(sql, params)

    result = add_auth_user_role(user_id=7, role="2", fetch_one=fetch, execute=lambda *_: 1)

    assert result["role_id"] == 2
    assert any("FROM roles WHERE id" in sql for sql, _ in seen)
    assert any(params == (2,) for _, params in seen)


def test_add_resout_role_par_slug_ou_name():
    seen = []

    def fetch(sql, params):
        seen.append((sql, params))
        return _fetch_for_roles(user={"id": 7}, role={"id": 3})(sql, params)

    result = add_auth_user_role(
        user_id=7,
        role="Admin",
        fetch_one=fetch,
        execute=lambda *_: 1,
    )

    assert result["role_id"] == 3
    assert any("slug" in sql and "name" in sql for sql, _ in seen)
    assert any(params == ("admin", "Admin", "admin") for _, params in seen)


def test_add_insere_dans_user_roles():
    executed = {}

    def execute(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    result = add_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(user={"id": 7}, role={"id": 2}),
        execute=execute,
    )

    assert result == {"user_id": 7, "role_id": 2, "created": True}
    assert "INSERT INTO user_roles" in executed["sql"]
    assert executed["params"] == (7, 2)


def test_add_ne_duplique_pas_association_existante():
    calls = []

    result = add_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(
            user={"id": 7},
            role={"id": 2},
            association={"user_id": 7, "role_id": 2},
        ),
        execute=lambda *args: calls.append(args),
    )

    assert result == {"user_id": 7, "role_id": 2, "created": False}
    assert calls == []


def test_add_refuse_utilisateur_absent():
    with pytest.raises(AuthAdminCliError, match="Utilisateur"):
        add_auth_user_role(
            user_id=99,
            role="admin",
            fetch_one=_fetch_for_roles(user=None, role={"id": 2}),
            execute=lambda *_: 1,
        )


def test_add_refuse_role_absent():
    with pytest.raises(AuthAdminCliError, match="Role"):
        add_auth_user_role(
            user_id=7,
            role="missing",
            fetch_one=_fetch_for_roles(user={"id": 7}, role=None),
            execute=lambda *_: 1,
        )


def test_add_refuse_id_et_email_ensemble():
    with pytest.raises(AuthAdminCliError, match="pas les deux"):
        add_auth_user_role(
            user_id=7,
            email="admin@example.test",
            role="admin",
            fetch_one=_fetch_for_roles(user={"id": 7}, role={"id": 2}),
            execute=lambda *_: 1,
        )


def test_add_exige_id_ou_email():
    with pytest.raises(AuthAdminCliError, match="--id ou --email"):
        add_auth_user_role(
            role="admin",
            fetch_one=_fetch_for_roles(user={"id": 7}, role={"id": 2}),
            execute=lambda *_: 1,
        )


def test_remove_supprime_association_existante():
    executed = {}

    def execute(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    result = remove_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(
            user={"id": 7},
            role={"id": 2},
            association={"user_id": 7, "role_id": 2},
        ),
        execute=execute,
    )

    assert result == {"user_id": 7, "role_id": 2, "removed": True}
    assert "DELETE FROM user_roles" in executed["sql"]
    assert executed["params"] == (7, 2)


def test_remove_est_propre_si_association_absente():
    calls = []

    result = remove_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(user={"id": 7}, role={"id": 2}, association=None),
        execute=lambda *args: calls.append(args),
    )

    assert result == {"user_id": 7, "role_id": 2, "removed": False}
    assert calls == []


def test_remove_ne_supprime_pas_users():
    executed = {}

    def execute(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    remove_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(
            user={"id": 7},
            role={"id": 2},
            association={"user_id": 7, "role_id": 2},
        ),
        execute=execute,
    )

    assert "DELETE FROM users" not in executed["sql"]


def test_remove_ne_supprime_pas_roles():
    executed = {}

    def execute(sql, params):
        executed["sql"] = sql
        executed["params"] = params
        return 1

    remove_auth_user_role(
        user_id=7,
        role="admin",
        fetch_one=_fetch_for_roles(
            user={"id": 7},
            role={"id": 2},
            association={"user_id": 7, "role_id": 2},
        ),
        execute=execute,
    )

    assert "DELETE FROM roles" not in executed["sql"]


def test_roles_liste_les_roles_utilisateur():
    roles = list_auth_user_roles(
        user_id=7,
        fetch_one=_fetch_for_roles(user={"id": 7}),
        fetch_all=lambda *_: [
            {"role_id": 2, "slug": "admin", "name": "Administrateur"},
            {"role_id": 3, "slug": "editor", "name": "Editeur"},
        ],
    )

    assert roles == (
        {"role_id": 2, "slug": "admin", "name": "Administrateur"},
        {"role_id": 3, "slug": "editor", "name": "Editeur"},
    )


def test_roles_affiche_etat_vide(monkeypatch, capsys):
    monkeypatch.setattr("cli.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_roles(
        ["--id", "7"],
        fetch_one=_fetch_for_roles(user={"id": 7}),
        fetch_all=lambda *_: [],
    )

    assert "Aucun role attribue" in capsys.readouterr().out


def test_cmd_role_add_affiche_message_idempotent(monkeypatch, capsys):
    monkeypatch.setattr("cli.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_role_add(
        ["--id", "7", "--role", "admin"],
        fetch_one=_fetch_for_roles(
            user={"id": 7},
            role={"id": 2},
            association={"user_id": 7, "role_id": 2},
        ),
        execute=lambda *_: 1,
    )

    assert "deja attribue" in capsys.readouterr().out


def test_cmd_role_remove_affiche_message_absent(monkeypatch, capsys):
    monkeypatch.setattr("cli.auth._load_env_and_configure_forge", lambda root: None)

    cmd_auth_user_role_remove(
        ["--id", "7", "--role", "admin"],
        fetch_one=_fetch_for_roles(user={"id": 7}, role={"id": 2}, association=None),
        execute=lambda *_: 1,
    )

    assert "absent" in capsys.readouterr().out


def test_aucune_interface_html():
    candidates = "\n".join(
        path.as_posix()
        for root in ("mvc/controllers", "mvc/views")
        for path in Path(root).rglob("*")
    )

    assert "auth_user_role" not in candidates
    assert "user_role" not in candidates


def test_aucune_route():
    source = Path("cli/auth.py").read_text(encoding="utf-8")

    assert "@route" not in source
    assert "Router" not in source


def test_aucun_formulaire_template():
    source = Path("cli/auth.py").read_text(encoding="utf-8")

    assert "Form(" not in source
    assert "render(" not in source
    assert ".html" not in source


def test_aucune_modification_rbac_historique():
    source = Path("packages/forge-mvc-rbac/forge_mvc_rbac/rbac.py").read_text(encoding="utf-8")

    assert "auth:user:role" not in source
    assert "user_roles" not in source
