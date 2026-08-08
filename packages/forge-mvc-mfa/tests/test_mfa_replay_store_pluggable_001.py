"""MFA-TOTP-REPLAY-SHARED-001 : le registre anti-rejeu devient enfichable.

Ces tests ne touchent pas la base. Ils vérifient trois choses.

Le **défaut ne bouge pas** : un projet qui ne fait rien garde le registre en
mémoire, avec sa limite. C'est la condition de la forme retenue.

Le **défaut est réellement limité** : deux registres en mémoire distincts
acceptent la même fenêtre, ce qui est exactement ce qui se produit derrière
gunicorn à plusieurs workers. Le test documente le défaut plutôt que de le
supposer.

L'**injection réachemine** les fonctions de module, sans quoi poser un magasin
partagé ne changerait rien au chemin d'appel réel de `verify_mfa_challenge`.

La preuve du partage entre processus est ailleurs, elle exige un vrai serveur :
`test_mfa_replay_db_integration_001.py`.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa import totp_replay


@pytest.fixture(autouse=True)
def _magasin_par_defaut() -> Iterator[None]:
    """Rend le magasin par défaut après chaque test.

    `set_replay_store` touche un état de module : sans restauration, un test
    contaminerait les suivants et le magasin posé fuirait dans toute la session.
    """
    yield
    totp_replay.reset_replay_store()


def test_le_defaut_est_le_registre_en_memoire() -> None:
    totp_replay.reset_replay_store()

    assert isinstance(totp_replay.get_replay_store(), totp_replay.InMemoryTotpReplayStore)


def test_deux_registres_en_memoire_ne_partagent_rien() -> None:
    """Le défaut mesuré, pas supposé : c'est la faille sous plusieurs workers.

    Chaque worker gunicorn tient son propre dictionnaire. Un même code TOTP
    valide est donc accepté une fois par worker.
    """
    worker_1 = totp_replay.InMemoryTotpReplayStore()
    worker_2 = totp_replay.InMemoryTotpReplayStore()

    assert worker_1.check_and_record(42, 1000) is True
    assert worker_1.check_and_record(42, 1000) is False, "le même worker doit refuser le rejeu"
    assert worker_2.check_and_record(42, 1000) is True, "un autre worker l'accepte : la faille"


def test_une_fenetre_anterieure_est_refusee() -> None:
    """Le contrat est plus fort que le refus du doublon exact.

    `verify_totp_code` tolère `valid_window=1`, donc le code de la fenêtre
    précédente reste valide. Sans cette règle il resterait rejouable après
    l'usage d'un code plus récent.
    """
    magasin = totp_replay.InMemoryTotpReplayStore()

    assert magasin.check_and_record(7, 2000) is True
    assert magasin.check_and_record(7, 1999) is False
    assert magasin.is_replay(7, 1999) is True


def test_l_injection_reroute_les_fonctions_de_module() -> None:
    """Sans ce réacheminement, poser un magasin ne changerait rien à `mfa.py`."""
    pose = totp_replay.InMemoryTotpReplayStore()
    totp_replay.set_replay_store(pose)

    assert totp_replay.get_replay_store() is pose
    assert totp_replay.check_and_record(3, 500) is True
    assert pose.is_replay(3, 500) is True, "le magasin posé doit avoir reçu l'écriture"
    assert totp_replay.is_replay(3, 500) is True


def test_un_identifiant_de_facteur_non_tracable_ne_bloque_pas() -> None:
    """Contrat conservé : ce qu'on ne sait pas tracer ne bloque pas l'authentification."""
    magasin = totp_replay.InMemoryTotpReplayStore()

    assert magasin.check_and_record(0, 10) is True
    assert magasin.check_and_record(0, 10) is True
    assert magasin.is_replay(0, 10) is False


def test_le_registre_en_memoire_satisfait_le_contrat() -> None:
    """Garde-fou : le défaut doit rester une mise en œuvre valide du protocole."""
    magasin: totp_replay.TotpReplayStore = totp_replay.InMemoryTotpReplayStore()

    assert magasin.check_and_record(1, 1) is True
    magasin.record_used(1, 2)
    assert magasin.is_replay(1, 2) is True
    assert magasin.purge_old(0.0) == 0
    magasin.purge_all()
    assert magasin.is_replay(1, 2) is False
