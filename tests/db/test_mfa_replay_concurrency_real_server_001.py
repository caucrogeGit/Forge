"""PREMORTEM-RC5-003 — l'anti-rejeu TOTP partagé tient sous concurrence réelle.

`MFA-TOTP-REPLAY-SHARED-001` promet que « deux requêtes concurrentes portant le
même code valide ne peuvent plus être acceptées toutes les deux ». Ses tests
d'origine vérifiaient la propriété **en séquence**, et par un adaptateur de
connexion écrit à la main.

Le pré-mortem de la rc5 a mis le magasin en concurrence réelle et trouvé deux
défauts que cette approche ne pouvait pas voir.

**Un interblocage InnoDB.** L'ordre d'origine tentait l'`INSERT` puis, sur
doublon, l'`UPDATE`. Or un `INSERT` qui échoue prend un verrou **partagé** sur
la ligne existante, et l'`UPDATE` qui suit en réclame un **exclusif** : douze
requêtes simultanées se bloquaient mutuellement et le moteur en tuait dix.
L'ordre est désormais inversé, l'`UPDATE` d'abord, l'`INSERT` en repli terminal.

**Un doublon non reconnu.** `core.database.db` **qualifie déjà** ses erreurs et
lève `UniqueViolationError` ; le module ne testait que `is_unique_violation()`,
qui interroge le backend sur une erreur **de pilote** et rend donc `False` face
au wrapper. Chaque rejeu remontait une erreur au client au lieu d'un refus
propre. L'adaptateur fait main des tests d'origine laissait passer l'erreur
brute du pilote, ce qui masquait entièrement le défaut.

Ce test passe donc par **`core.database.db`**, la couche de production, et non
par un adaptateur. C'est la condition pour qu'il ait une valeur de preuve.
"""
from __future__ import annotations

import threading
import uuid

import pytest

from core.database import db

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_mfa")

#: Nombre de requêtes lancées ensemble. Au delà d'une poignée, les motifs de
#: verrouillage d'InnoDB se manifestent ; en dessous, ils se cachent.
CONCURRENTS = 16


def _table_temporaire() -> str:
    return f"forge_it_replay_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def magasin(real_db: None):
    """Un `DbTotpReplayStore` sur une table jetable, via la vraie couche.

    La table du paquet a un nom fixe. On en crée une jetable et on aiguille le
    module dessus le temps du test, pour ne pas dépendre d'un provisionnement
    ni polluer une base partagée.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_mfa import replay_store_db
    from forge_mvc_mfa.tables import TOTP_REPLAY

    nom = _table_temporaire()
    jetable = type(TOTP_REPLAY)(
        name=nom,
        columns=TOTP_REPLAY.columns,
        primary_key=TOTP_REPLAY.primary_key,
        indexes=(),
    )
    for instruction in render_create_table(jetable, get_backend().dialect):
        db.execute(instruction, ())

    anciens = (
        replay_store_db._INSERT_SQL,  # pyright: ignore[reportPrivateUsage]
        replay_store_db._ADVANCE_SQL,  # pyright: ignore[reportPrivateUsage]
        replay_store_db._SELECT_SQL,  # pyright: ignore[reportPrivateUsage]
    )
    cible = TOTP_REPLAY.name
    replay_store_db._INSERT_SQL = anciens[0].replace(cible, nom)  # pyright: ignore[reportPrivateUsage]
    replay_store_db._ADVANCE_SQL = anciens[1].replace(cible, nom)  # pyright: ignore[reportPrivateUsage]
    replay_store_db._SELECT_SQL = anciens[2].replace(cible, nom)  # pyright: ignore[reportPrivateUsage]
    try:
        yield replay_store_db.DbTotpReplayStore()
    finally:
        (
            replay_store_db._INSERT_SQL,  # pyright: ignore[reportPrivateUsage]
            replay_store_db._ADVANCE_SQL,  # pyright: ignore[reportPrivateUsage]
            replay_store_db._SELECT_SQL,  # pyright: ignore[reportPrivateUsage]
        ) = anciens
        db.execute(f"DROP TABLE IF EXISTS {nom}", ())


def _course(magasin, facteur: int, fenetre: int) -> tuple[list[bool], list[str]]:
    """Lance `CONCURRENTS` requêtes au même instant sur le même code."""
    acceptations: list[bool] = []
    erreurs: list[str] = []
    verrou = threading.Lock()
    depart = threading.Barrier(CONCURRENTS)

    def requete() -> None:
        depart.wait()
        try:
            resultat = magasin.check_and_record(facteur, fenetre)
            with verrou:
                acceptations.append(resultat)
        except Exception as exc:  # noqa: BLE001 — c'est précisément ce qu'on mesure
            with verrou:
                erreurs.append(f"{type(exc).__name__}: {exc}")

    fils = [threading.Thread(target=requete) for _ in range(CONCURRENTS)]
    for f in fils:
        f.start()
    for f in fils:
        f.join()
    return acceptations, erreurs


def test_un_seul_code_accepte_sur_un_facteur_neuf(magasin) -> None:
    """LE test du ticket, en conditions de course."""
    acceptations, erreurs = _course(magasin, facteur=1, fenetre=1000)

    assert not erreurs, f"aucune requête ne doit lever : {erreurs[:3]}"
    assert sum(1 for a in acceptations if a) == 1, "exactement une acceptation"
    assert len(acceptations) == CONCURRENTS


def test_un_seul_code_accepte_sur_un_facteur_deja_vu(magasin) -> None:
    """Chemin de l'`UPDATE`, celui de l'interblocage d'origine.

    Le facteur a déjà une ligne, donc toutes les requêtes passent par le même
    `UPDATE` gardé. C'est le cas qui déclenchait le verrouillage croisé.
    """
    magasin.check_and_record(2, 2000)

    acceptations, erreurs = _course(magasin, facteur=2, fenetre=2001)

    assert not erreurs, f"aucune requête ne doit lever : {erreurs[:3]}"
    assert sum(1 for a in acceptations if a) == 1


def test_un_rejeu_est_refuse_proprement_et_non_par_une_erreur(magasin) -> None:
    """Le second défaut : le doublon doit devenir un refus, pas une exception.

    `core.database.db` lève `UniqueViolationError`, forme déjà qualifiée.
    Interroger `is_unique_violation()` sur elle rend `False`, et l'erreur
    remontait donc jusqu'au client.
    """
    assert magasin.check_and_record(3, 3000) is True
    assert magasin.check_and_record(3, 3000) is False


def test_une_fenetre_anterieure_est_refusee_par_la_vraie_couche(magasin) -> None:
    assert magasin.check_and_record(4, 4000) is True
    assert magasin.check_and_record(4, 3999) is False
    assert magasin.is_replay(4, 3999) is True
