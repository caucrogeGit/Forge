"""MARIADB-LOCK-WAIT-503-001, mesure sur serveur réel.

Les errno d'un pilote ne sont contractuels nulle part : seul un test qui tient
réellement le verrou prouve que la reconnaissance tient encore. Le protocole
verrouille une ligne depuis une première transaction, puis la fait convoiter
par une seconde dont `innodb_lock_wait_timeout` est réduit à une seconde.

Le pendant hors base est `tests/test_mariadb_lock_wait_503_001.py`.
"""
from __future__ import annotations

import threading
import time
from typing import Any

import pytest

pytestmark = pytest.mark.db

_TABLE = "forge_lock_wait_probe"


@pytest.fixture()
def table_verrouillable(real_db: None):
    from core.database import db

    db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
    db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT) ENGINE=InnoDB")
    db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0), (2, 0)")
    yield
    db.execute(f"DROP TABLE IF EXISTS {_TABLE}")


def test_l_attente_de_verrou_devient_une_indisponibilite(
    table_verrouillable: None,
) -> None:
    """Le cas mesuré : errno 1205 traversait jusqu'à la page 500."""
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError
    from core.database.transaction import transaction

    backend = get_backend()
    # Le verrou est tenu hors de la couche Forge, par une connexion à part :
    # deux emprunts au même pool suffiraient, mais la transaction du bloc doit
    # rester celle qui attend, pas celle qui bloque.
    bloqueur: Any = backend.get_connection()
    bloqueur.autocommit = False
    curseur = bloqueur.cursor()
    curseur.execute(f"SELECT v FROM {_TABLE} WHERE id = 1 FOR UPDATE")

    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            db.execute("SET innodb_lock_wait_timeout = 1", tx=tx)
            db.execute(f"UPDATE {_TABLE} SET v = 1 WHERE id = 1", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture
    finally:
        curseur.close()
        bloqueur.rollback()
        backend.close_connection(bloqueur)

    assert erreur is not None, "le verrou tenu devrait faire échouer l'écriture"
    assert isinstance(erreur, DatabaseUnavailableError), (
        f"attendu une indisponibilité, obtenu "
        f"{type(erreur).__module__}.{type(erreur).__name__} : {erreur}"
    )


def test_l_ecriture_repasse_une_fois_le_verrou_rendu(
    table_verrouillable: None,
) -> None:
    """La condition est passagère : c'est ce qui justifie le 503."""
    from core.database import db

    assert db.execute(f"UPDATE {_TABLE} SET v = 2 WHERE id = 1") == 1


def test_l_interblocage_reste_une_erreur_du_serveur(
    table_verrouillable: None,
) -> None:
    """Deux transactions croisées : InnoDB en annule une, errno 1213.

    Il ne doit pas être qualifié : attendre n'y change rien, et le remède est
    de revoir l'ordre de prise des verrous.
    """
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError

    backend = get_backend()
    captures: "list[BaseException]" = []
    verrou = threading.Lock()

    def croise(premier: int, second: int) -> None:
        connexion: Any = backend.get_connection()
        connexion.autocommit = False
        try:
            curseur = connexion.cursor()
            curseur.execute(f"UPDATE {_TABLE} SET v = v + 1 WHERE id = {premier}")
            time.sleep(0.3)
            curseur.execute(f"UPDATE {_TABLE} SET v = v + 1 WHERE id = {second}")
            connexion.commit()
            curseur.close()
        except BaseException as erreur:  # noqa: BLE001 — c'est le sujet du test
            with verrou:
                captures.append(erreur)
            try:
                connexion.rollback()
            except Exception:  # noqa: BLE001 — annulation best-effort
                pass
        finally:
            backend.close_connection(connexion)

    fils = [threading.Thread(target=croise, args=(1, 2)),
            threading.Thread(target=croise, args=(2, 1))]
    for f in fils:
        f.start()
    for f in fils:
        f.join()

    if not captures:
        pytest.skip("aucun interblocage déclenché : ordonnancement trop favorable")

    erreur = captures[0]
    assert getattr(erreur, "errno", None) == 1213, f"errno inattendu : {erreur}"
    assert backend.is_unavailable(erreur) is False, (
        "l'interblocage ne doit pas passer pour une indisponibilité passagère"
    )
    assert not isinstance(erreur, DatabaseUnavailableError)
