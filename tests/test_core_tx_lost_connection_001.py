"""CORE-TX-LOST-CONNECTION-001 : un bloc `transaction()` ne rend jamais l'exception du pilote.

`DB-CONNECTION-LOST-503-001` avait protégé l'annulation de `core.database.db`,
parce que sur connexion coupée le rollback échoue lui aussi et remplace la
cause par la sienne. Le même chemin existait dans `core.database.transaction`,
non protégé. Mesuré en tuant la session pendant le bloc, sur les trois backends
serveur :

    MariaDB      mariadb.InterfaceError      contexte : DatabaseUnavailableError
    PostgreSQL   psycopg.OperationalError    contexte : OperationalError
    SQL Server   pyodbc.OperationalError     contexte : DatabaseUnavailableError

La bonne erreur avait donc été construite dans deux cas sur trois, et le
rollback l'avait écrasée. Double conséquence : un 500 au lieu du 503, et la
rupture de la promesse de l'ADR-054, l'application recevant une exception
propre au pilote qu'elle ne peut attraper sans se lier à lui.

Le CRUD généré est directement concerné : les fonctions `add` et `sync` des
relations many-to-many ouvrent un `transaction()`.

Trois sorties doivent laisser la connexion partir, faute de quoi son jeton de
file d'attente est perdu et la capacité du pool baisse définitivement : l'échec
de l'armement, celui de l'annulation et celui de la restauration d'autocommit.

Le pendant sur serveurs réels est `tests/db/test_tx_lost_connection_real_server_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.database import db, qualify, transaction as tx_module
from core.database.errors import DatabaseUnavailableError, UniqueViolationError
from core.database.transaction import transaction


class _BackendFactice:
    """Backend minimal dont on pilote les deux réponses."""

    def __init__(self, *, perdue: bool = False, doublon: bool = False) -> None:
        self._perdue = perdue
        self._doublon = doublon

    def is_unavailable(self, error: Exception) -> bool:
        return self._perdue

    def is_unique_violation(self, error: Exception) -> bool:
        return self._doublon


class _Connexion:
    """Connexion instrumentée : chaque étape peut être rendue défaillante."""

    def __init__(
        self,
        *,
        rollback_leve: bool = False,
        commit_leve: bool = False,
        autocommit_leve: bool = False,
        armement_leve: bool = False,
    ) -> None:
        self._rollback_leve = rollback_leve
        self._commit_leve = commit_leve
        self._autocommit_leve = autocommit_leve
        self._armement_leve = armement_leve
        self._autocommit: Any = True
        self.rollbacks = 0
        self.commits = 0
        self.rendue = False

    @property
    def autocommit(self) -> Any:
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value: Any) -> None:
        if self._armement_leve and value is False:
            raise RuntimeError("connexion morte : autocommit refusé")
        if self._autocommit_leve and value is not False:
            raise RuntimeError("connexion morte : autocommit refusé")
        self._autocommit = value

    def cursor(self, **_: Any) -> Any:
        raise AssertionError("le test n'exécute aucune requête")

    def rollback(self) -> None:
        self.rollbacks += 1
        if self._rollback_leve:
            raise RuntimeError("rollback impossible : connexion morte")

    def commit(self) -> None:
        self.commits += 1
        if self._commit_leve:
            raise RuntimeError("commit impossible : connexion morte")


def _brancher(monkeypatch: pytest.MonkeyPatch, backend: _BackendFactice,
              connexion: _Connexion) -> None:
    monkeypatch.setattr(qualify, "get_backend", lambda: backend)
    monkeypatch.setattr(tx_module, "get_connection", lambda: connexion)

    def _rendre(_c: Any) -> None:
        connexion.rendue = True

    monkeypatch.setattr(tx_module, "close_connection", _rendre)


# ── L'annulation ne masque plus la cause ─────────────────────────────────────

def test_une_annulation_impossible_ne_masque_pas_la_coupure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le cas mesuré : `mariadb.InterfaceError` sortait à la place du 503."""
    connexion = _Connexion(rollback_leve=True)
    _brancher(monkeypatch, _BackendFactice(perdue=True), connexion)

    with pytest.raises(DatabaseUnavailableError):
        with transaction():
            raise RuntimeError("la connexion vient d'être coupée")

    assert connexion.rollbacks == 1, "l'annulation doit rester tentée"


def test_une_annulation_impossible_ne_masque_pas_un_doublon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La faute d'origine peut aussi être actionnable par l'utilisateur."""
    connexion = _Connexion(rollback_leve=True)
    _brancher(monkeypatch, _BackendFactice(doublon=True), connexion)

    with pytest.raises(UniqueViolationError):
        with transaction():
            raise RuntimeError("doublon rendu par le pilote")


def test_une_erreur_deja_qualifiee_traverse_inchangee(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_run_query` qualifie déjà : le bloc ne doit pas la requalifier."""
    connexion = _Connexion()
    _brancher(monkeypatch, _BackendFactice(), connexion)
    origine = DatabaseUnavailableError("connexion perdue")

    with pytest.raises(DatabaseUnavailableError) as capture:
        with transaction():
            raise origine

    assert capture.value is origine


def test_le_reste_remonte_inchange(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le cœur n'enveloppe que ce qu'il sait qualifier (ADR-054)."""
    connexion = _Connexion()
    _brancher(monkeypatch, _BackendFactice(), connexion)

    with pytest.raises(ValueError, match="faute applicative"):
        with transaction():
            raise ValueError("faute applicative")


# ── La validation est qualifiée comme une requête ────────────────────────────

def test_un_commit_sur_connexion_morte_devient_une_indisponibilite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le corps a réussi, la validation échoue : c'est la même famille."""
    connexion = _Connexion(commit_leve=True)
    _brancher(monkeypatch, _BackendFactice(perdue=True), connexion)

    with pytest.raises(DatabaseUnavailableError):
        with transaction():
            pass


def test_un_commit_en_doublon_reste_un_doublon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une contrainte différée saute à la validation, pas à l'insertion."""
    connexion = _Connexion(commit_leve=True)
    _brancher(monkeypatch, _BackendFactice(doublon=True), connexion)

    with pytest.raises(UniqueViolationError):
        with transaction():
            pass


def test_l_erreur_traduite_conserve_sa_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    connexion = _Connexion(commit_leve=True)
    _brancher(monkeypatch, _BackendFactice(perdue=True), connexion)

    with pytest.raises(DatabaseUnavailableError) as capture:
        with transaction():
            pass

    assert isinstance(capture.value.__cause__, RuntimeError)


# ── Aucune sortie ne retient la connexion ────────────────────────────────────

def test_un_armement_impossible_rend_la_connexion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le pool peut livrer une connexion que le serveur a déjà fermée.

    Sans garde, l'exception sortait avant le `try` et la connexion n'était
    jamais rendue : son jeton de file d'attente était perdu.
    """
    connexion = _Connexion(armement_leve=True)
    _brancher(monkeypatch, _BackendFactice(perdue=True), connexion)

    with pytest.raises(DatabaseUnavailableError):
        with transaction():
            pytest.fail("le corps ne doit pas s'exécuter")

    assert connexion.rendue, "la connexion doit repartir malgré l'échec d'armement"


def test_une_restauration_impossible_rend_la_connexion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La restauration d'autocommit est la dernière étape avant la restitution."""
    connexion = _Connexion(autocommit_leve=True)
    _brancher(monkeypatch, _BackendFactice(), connexion)

    with transaction():
        pass

    assert connexion.rendue, "la connexion doit repartir malgré l'échec de restauration"


def test_une_annulation_impossible_rend_la_connexion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connexion = _Connexion(rollback_leve=True, autocommit_leve=True)
    _brancher(monkeypatch, _BackendFactice(perdue=True), connexion)

    with pytest.raises(DatabaseUnavailableError):
        with transaction():
            raise RuntimeError("coupure")

    assert connexion.rendue


def test_la_sortie_nominale_rend_la_connexion(monkeypatch: pytest.MonkeyPatch) -> None:
    connexion = _Connexion()
    _brancher(monkeypatch, _BackendFactice(), connexion)

    with transaction():
        pass

    assert connexion.commits == 1
    assert connexion.rollbacks == 0
    assert connexion.rendue
    assert connexion.autocommit is True, "l'état initial doit être restauré"


# ── La fermeture du curseur ne retient plus la connexion non plus ────────────

def test_un_curseur_qui_refuse_de_se_fermer_ne_retient_pas_la_connexion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Même famille, côté `db` : le `finally` ferme le curseur avant de rendre.

    Une fermeture qui lève y sautait la restitution, donc perdait le jeton.
    """
    rendues: list[Any] = []

    class _CurseurRetif:
        def execute(self, *_a: Any, **_k: Any) -> None:
            return None

        def fetchone(self) -> Any:
            return {"v": 1}

        def close(self) -> None:
            raise RuntimeError("curseur mort")

    class _Connexion2:
        def cursor(self, **_: Any) -> Any:
            return _CurseurRetif()

        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

    monkeypatch.setattr(qualify, "get_backend", lambda: _BackendFactice())
    monkeypatch.setattr(db, "get_connection", _Connexion2)
    monkeypatch.setattr(db, "close_connection", rendues.append)

    assert db.fetch_one("SELECT 1") == {"v": 1}
    assert len(rendues) == 1, "la connexion doit être rendue malgré le curseur mort"


# ── La traduction a un seul foyer ────────────────────────────────────────────

def test_la_qualification_est_partagee_par_les_deux_chemins() -> None:
    """La cause du défaut était une traduction privée à `db` (règle A)."""
    from pathlib import Path

    source_tx = Path(tx_module.__file__).read_text(encoding="utf-8")
    source_db = Path(db.__file__).read_text(encoding="utf-8")

    assert "from core.database.qualify import raise_qualified" in source_tx
    assert "from core.database.qualify import raise_qualified" in source_db
