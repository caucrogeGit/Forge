"""Le parcours de connexion, du WSGI à la base (AUTH-WSGI-LOGIN-REAL-001).

Ce fichier réunit tout ce que le cycle a changé et l'exerce d'un bout à l'autre,
par le **chemin de production** : une requête WSGI entre, un mot de passe est
vérifié contre une vraie base, un événement d'audit sort.

Trois changements se rencontrent ici, et aucun n'était vérifié ensemble.

L'identité de connexion est passée de `email` à `login` (ADR-089), et le loader
qu'engendre `make:auth` interroge `WHERE login = ?`.

Le cœur émet désormais `login.success` et `login.failed` (ADR-091), l'échec
portant sa raison, car `authenticate_user` est le seul à savoir pourquoi une
connexion échoue.

Les horodatages du compte sont posés en UTC naïf (`TIMESTAMPS-NAIVE-UTC-001`).

La leçon qui a motivé ce fichier : un jumeau de test ne prouve rien sur ce que
sert la production. Une sonde `/health` au contrat de stabilité a déjà répondu
404 sous WSGI alors que tous ses tests passaient.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.auth.password import hash_password
from core.auth.session import authenticate_user
from core.database.table_ddl import Column, TableDefinition
from core.database.timestamps import utc_now
from core.http.request import Request
from core.http.response import Response
from core.http.router import Router
from forge_mvc_testing.real_db import tables_temporaires

#: Table `users` du socle, dans la forme qu'elle a depuis l'ADR-089 : `login`
#: porte l'identité, `email` le contact facultatif.
USERS = TableDefinition(
    name="users",
    columns=[
        Column("id", "identity"),
        Column("login", "string", length=255),
        Column("email", "string", length=255, nullable=True),
        Column("password_hash", "string", length=255),
        Column("is_active", "boolean"),
        Column("created_at", "datetime"),
        Column("updated_at", "datetime"),
    ],
    primary_key=["id"],
)

#: Une identité qui n'est pas une adresse, et qui porte des capitales : les
#: deux propriétés que le cycle a rendues possibles.
_IDENTITE = "2TNE1-01"
_MOT_DE_PASSE = "secret123"


def _environ(corps: bytes) -> "dict[str, Any]":
    return {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/login",
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_LENGTH": str(len(corps)),
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "wsgi.input": BytesIO(corps),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }


@pytest.fixture
def base(real_backend_db: str):
    with tables_temporaires(USERS) as db:
        maintenant = utc_now()
        db.execute(
            "INSERT INTO users (login, password_hash, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (_IDENTITE, hash_password(_MOT_DE_PASSE), True, maintenant, maintenant),
        )
        yield db


def _application(db: Any, vus: "list[Any]"):
    """Application WSGI minimale portant le loader qu'engendre `make:auth`."""

    def load_user_by_login(login: str) -> "dict[str, Any] | None":
        return db.fetch_one(
            "SELECT id, login, email, password_hash, is_active FROM users WHERE login = ?",
            (login,),
        )

    def connexion(request: Request) -> Response:
        user = authenticate_user(
            request.form("login", ""), request.form("password", ""), load_user_by_login
        )
        vus.append(user)
        return Response(
            200, "ok" if user else "ko", content_type="text/plain; charset=utf-8"
        )

    router = Router()
    router.add("POST", "/login", connexion, public=True, csrf=False)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


def _sans_reponse(status: str, headers: Any, exc_info: Any = None):
    return lambda chunk: None


def test_une_identite_sans_arobase_se_connecte(base: Any) -> None:
    """LE test du cycle : `2TNE1-01` est une identité, pas une adresse.

    La casse est conservée, ce qui rouvre la connexion sur SQLite, et rien
    n'exige un `@`, ce que la CLI imposait encore.
    """
    vus: "list[Any]" = []
    app = _application(base, vus)

    app(_environ(f"login={_IDENTITE}&password={_MOT_DE_PASSE}".encode()), _sans_reponse)

    assert vus[0] is not None, "la connexion valide échoue par le chemin WSGI"
    assert vus[0].login == _IDENTITE
    assert vus[0].email is None, "ce compte n'a pas de contact, et c'est valide"


def test_les_trois_evenements_sortent_avec_leur_raison(base: Any, caplog: Any) -> None:
    """`login.success` en INFO, `login.failed` en WARNING, et l'échec distingue.

    Le compte trouvé mais mot de passe faux porte son `user_id` ; le compte
    inconnu n'en a pas. C'est cette distinction que le contrôleur ne pouvait
    pas faire, ne recevant qu'un `None`, et qui justifie l'émission depuis le
    cœur (ADR-091).
    """
    vus: "list[Any]" = []
    app = _application(base, vus)

    with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
        app(_environ(f"login={_IDENTITE}&password={_MOT_DE_PASSE}".encode()), _sans_reponse)
        app(_environ(f"login={_IDENTITE}&password=faux".encode()), _sans_reponse)
        app(_environ(b"login=INCONNU&password=x"), _sans_reponse)

    evenements = [r.getMessage() for r in caplog.records if r.name == "forge.auth.audit"]

    assert len(evenements) == 3, f"trois tentatives, trois événements, vu {len(evenements)}"
    assert "login.success user_id=1" in evenements[0]
    assert "login.failed user_id=1" in evenements[1], "un mot de passe faux nomme le compte"
    assert "login.failed user_id=None" in evenements[2], "un compte inconnu n'en a pas"


def test_aucun_evenement_ne_porte_le_mot_de_passe(base: Any, caplog: Any) -> None:
    """La règle de l'ADR-091, tenue là où elle peut être violée.

    Ni le mot de passe, ni la valeur saisie quand elle a échoué : une faute de
    frappe sur un mot de passe ressemble trop à un mot de passe.
    """
    vus: "list[Any]" = []
    app = _application(base, vus)

    with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
        app(_environ(f"login={_IDENTITE}&password=MonSecretQuiFuite".encode()), _sans_reponse)

    trace = " ".join(r.getMessage() for r in caplog.records)

    assert "MonSecretQuiFuite" not in trace
    assert _MOT_DE_PASSE not in trace
