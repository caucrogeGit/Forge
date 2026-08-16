"""Tests AUTH-USER-002 — table users optionnelle Forge."""

from pathlib import Path

import forge

from core.auth import (
    AuthError,
    AuthUser,
    InvalidAuthUserError,
    is_valid_auth_user,
    normalize_auth_user,
    validate_auth_user_contract,
)
from cli.security.auth import USERS_SQL, cmd_auth_init


# AUTH-DDL-TESTS-SOURCE-001 : les assertions de contenu portent sur USERS_SQL,
# la constante canonique, et non sur cette fixture. La fixture est une COPIE,
# tenue par `test_auth_ddl_fixture_parity_001` ; elle a dérivé pendant deux
# tickets sans que rien ne le voie. Ce chemin ne sert donc plus qu'à vérifier
# que le projet d'exemple porte bien le fichier.
SQL_FILE = Path("tests/fixtures/app/mvc/models/sql/users.sql")


def _normalized_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_users_sql_file_exists():
    assert SQL_FILE.exists()


def test_users_sql_contains_create_table():
    assert "CREATE TABLE IF NOT EXISTS users" in USERS_SQL


def test_users_sql_contains_id_primary_key():
    sql = _normalized_sql(USERS_SQL)
    assert "id INT AUTO_INCREMENT PRIMARY KEY" in sql


def test_users_sql_login_porte_identite_et_email_reste_contact():
    """`login` porte l'identité, `email` le contact (ADR-089).

    Ce test exigeait auparavant `email VARCHAR(255) NOT NULL UNIQUE`, donc
    l'inverse de la règle en vigueur : il lisait une fixture restée à l'état
    d'avant l'ADR-089, si bien qu'il restait vert en affirmant une règle abrogée.
    """
    sql = _normalized_sql(USERS_SQL)
    assert "login VARCHAR(255) NOT NULL UNIQUE" in sql
    assert "email VARCHAR(255) NULL" in sql
    # Le contact n'est ni obligatoire ni unique : deux comptes peuvent partager
    # une adresse, et un compte peut ne pas en avoir.
    assert "email VARCHAR(255) NOT NULL" not in sql


def test_users_sql_contains_password_hash():
    sql = _normalized_sql(USERS_SQL)
    assert "password_hash VARCHAR(255) NOT NULL" in sql


def test_users_sql_contains_is_active_default():
    sql = _normalized_sql(USERS_SQL)
    assert "is_active BOOLEAN NOT NULL DEFAULT TRUE" in sql


def test_users_sql_contains_email_verified_at():
    sql = _normalized_sql(USERS_SQL)
    assert "email_verified_at DATETIME NULL" in sql


def test_users_sql_ne_porte_plus_last_login_at():
    """La colonne est retirée (ADR-091, `AUTH-EVENTS-EMIT-001`).

    Créée par le cœur et écrite par personne, elle supposait un écrivain que le
    cœur n'a pas : il n'écrit nulle part ailleurs dans `users`. Le journal
    d'authentification répond à la même question, avec la raison de l'échec.

    Ce test exigeait la colonne, et restait vert sur une fixture périmée.
    """
    sql = _normalized_sql(USERS_SQL)
    assert "last_login_at" not in sql


def test_users_sql_contains_created_at():
    """`NOT NULL` sans défaut : Python est l'autorité (ADR-081).

    Ce test exigeait `DEFAULT CURRENT_TIMESTAMP`, donc figeait l'écart entre le
    socle et la règle que Forge impose partout ailleurs
    (`AUTH-TIMESTAMPS-REMOVE-DEFAULTS-001`).
    """
    sql = _normalized_sql(USERS_SQL)
    assert "created_at DATETIME NOT NULL" in sql
    assert "created_at DATETIME NOT NULL DEFAULT" not in sql


def test_users_sql_contains_updated_at():
    """Sans `ON UPDATE` non plus : Python decide aussi de la mise a jour.

    C'est la seconde moitie de la double horloge que l'ADR-081 refuse.
    """
    sql = _normalized_sql(USERS_SQL)
    assert "updated_at DATETIME NOT NULL" in sql
    assert "ON UPDATE CURRENT_TIMESTAMP" not in sql


def test_auth_init_creates_users_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    sql_file = tmp_path / "mvc" / "models" / "sql" / "users.sql"
    assert sql_file.exists()
    assert sql_file.read_text(encoding="utf-8") == USERS_SQL


def test_auth_init_avertit_sur_users_sql_divergent(tmp_path, capsys):
    # CLI-SCAFFOLD-PRIMITIVE-001 : un fichier existant au contenu DIFFÉRENT est
    # signalé (averti), jamais écrasé.
    sql_file = tmp_path / "mvc" / "models" / "sql" / "users.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text("-- custom", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "diffère" in out  # averti (le contenu diverge)
    assert sql_file.read_text(encoding="utf-8") == "-- custom"  # jamais écrasé


def test_forge_auth_init_is_dispatched(monkeypatch):
    captured = {}

    def fake_auth_main(args):
        captured["args"] = args

    monkeypatch.setattr("sys.argv", ["forge", "auth:init"])
    monkeypatch.setattr(forge, "auth_main", fake_auth_main)

    forge.main()

    assert captured["args"] == ["auth:init"]


def test_auth_init_does_not_create_user_account(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.rglob("*") if path.is_file())
    assert "INSERT INTO users" not in generated
    assert "admin" not in generated.lower()


def test_auth_init_does_not_create_session(monkeypatch, tmp_path):
    import core.security.session as session_module

    calls = []
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")

    cmd_auth_init([], root=tmp_path)

    assert calls == []


def test_auth_init_does_not_modify_rbac(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated_paths = {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()}
    assert "mvc/models/sql/users.sql" in generated_paths
    assert all("rbac" not in path.lower() for path in generated_paths)
    assert "mvc/models/sql/user_roles.sql" in generated_paths


def test_auth_init_ponts_optin_skippes_si_absents(tmp_path, monkeypatch, capsys):
    # FORGE-4 : sans les opt-ins mfa/rbac, leurs ponts SQL (FK vers roles/mfa) ne
    # sont pas écrits ; le socle de base l'est, et le skip est annoncé.
    import cli.security.auth as auth
    monkeypatch.setattr(auth, "_optin_installed", lambda name: False)
    auth.cmd_auth_init([], root=tmp_path)
    generated = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}
    assert "mvc/models/sql/users.sql" in generated
    assert "mvc/models/sql/auth_tokens.sql" in generated
    assert "mvc/models/sql/auth_audit_log.sql" in generated
    assert "mvc/models/sql/auth_rate_limit_attempts.sql" in generated
    assert "mvc/models/sql/user_roles.sql" not in generated
    assert "mvc/models/sql/auth_mfa_factors.sql" not in generated
    assert "mvc/models/sql/auth_mfa_recovery_codes.sql" not in generated
    assert "non installé" in capsys.readouterr().out


def test_auth_init_ponts_optin_ecrits_si_presents(tmp_path, monkeypatch):
    # Symétrique : opt-ins présents, les ponts sont écrits.
    import cli.security.auth as auth
    monkeypatch.setattr(auth, "_optin_installed", lambda name: True)
    auth.cmd_auth_init([], root=tmp_path)
    generated = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}
    assert "mvc/models/sql/user_roles.sql" in generated
    assert "mvc/models/sql/auth_mfa_factors.sql" in generated
    assert "mvc/models/sql/auth_mfa_recovery_codes.sql" in generated


def test_auth_user_existing_contract_stays_compatible():
    user = AuthUser(id=1, login="a@b.com", password_hash="hash")
    assert user.is_active is True
    assert user.created_at is None
    assert user.updated_at is None
    assert is_valid_auth_user(user) is True


def test_core_auth_public_imports_stay_stable():
    user = normalize_auth_user({"id": 1, "login": " a@b.com ", "password_hash": "hash"})
    assert user == AuthUser(id=1, login="a@b.com", password_hash="hash")
    assert validate_auth_user_contract(user) is None
    assert issubclass(InvalidAuthUserError, AuthError)
