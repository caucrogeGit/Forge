"""FIXTURES-PG-FK-PRIVILEGE-001 : un droit refusé est reconnu, pas rendu en trace.

`fixtures:load --no-fk-checks` et `fixtures:purge` encadrent leur travail par le
levier du dialecte. Sur PostgreSQL, ce levier est
`SET session_replication_role`, qui **exige un rôle superutilisateur**. Or
l'ADR-033 fait tourner l'applicatif en compte DML strict : dans la configuration
que Forge recommande, l'option est donc refusée par le serveur.

Ce que ces tests vérifient tient en deux points.

Le backend **reconnaît** un refus de droit, à son signal propre et non à son
texte, PostgreSQL traduisant ses messages.

Les deux commandes **s'arrêtent en nommant la cause**, au lieu de laisser
l'exception du pilote traverser jusqu'à une trace Python.

Le test se connecte avec un rôle ordinaire, jamais en `postgres` : la fixture
`real_pg_db` est superutilisateur, et un test écrit dessus passerait sans rien
prouver. C'est exactement ce qui a laissé vivre le défaut.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.db, pytest.mark.db_pg]


def _projet_avec_une_fixture(racine) -> None:
    """Monte un projet minimal chargeable, table comprise.

    Sans la table, les commandes échoueraient sur l'`INSERT` et le test
    prouverait autre chose que le droit refusé.
    """
    import core.database.db as db

    db.execute("DROP TABLE IF EXISTS ville")
    db.execute("CREATE TABLE ville (id SERIAL PRIMARY KEY, nom VARCHAR(80))")
    dossier = racine / "mvc" / "fixtures"
    dossier.mkdir(parents=True)
    (dossier / "ville.sql").write_text(
        "INSERT INTO ville (nom) VALUES ('Lyon');", encoding="utf-8"
    )


def _sans_privilege() -> Exception:
    """Provoque le refus réel, et retourne l'exception du pilote."""
    import core.database.db as db

    try:
        db.execute("SET session_replication_role = replica")
    except Exception as error:  # noqa: BLE001 — c'est l'objet du test
        return error
    pytest.fail(
        "SET session_replication_role a été accepté : le rôle de test est "
        "privilégié, donc ce test ne prouverait rien."
    )


def test_le_role_de_test_est_bien_ordinaire(real_pg_db_sans_privilege: str) -> None:
    """Contrôle du contrôle : sans lui, tout le fichier serait creux.

    Si la fixture rendait un jour un rôle privilégié, les tests suivants
    passeraient pour la mauvaise raison. Ce test échouerait, lui.
    """
    import core.database.db as db

    lignes = db.fetch_all("SELECT rolsuper FROM pg_roles WHERE rolname = CURRENT_USER")
    assert lignes, "le rôle courant est introuvable dans pg_roles"
    assert not list(lignes[0].values())[0], (
        f"{real_pg_db_sans_privilege} est superutilisateur : le test serait creux."
    )


def test_le_backend_reconnait_le_refus_de_droit(
    real_pg_db_sans_privilege: str,
) -> None:
    """Le refus est qualifié par le contrat, à son SQLSTATE et non à son texte."""
    from core.database.backend import get_backend

    erreur = _sans_privilege()
    assert get_backend().is_insufficient_privilege_error(erreur), (
        f"refus de droit non reconnu : {type(erreur).__name__} "
        f"sqlstate={getattr(erreur, 'sqlstate', None)}"
    )


def test_un_refus_de_droit_ne_se_confond_pas_avec_une_requete_fautive(
    real_pg_db_sans_privilege: str,
) -> None:
    """Stricture : dans le doute, faux.

    Un faux positif ferait annoncer un droit manquant là où la requête est
    simplement fautive, et enverrait chercher du côté des permissions.
    """
    import core.database.db as db
    from core.database.backend import get_backend

    backend = get_backend()
    try:
        db.execute("SELECT * FROM table_qui_n_existe_pas_du_tout")
    except Exception as error:  # noqa: BLE001 — c'est l'objet du test
        assert not backend.is_insufficient_privilege_error(error)
    else:
        pytest.fail("la requête fautive aurait dû échouer")


def test_load_no_fk_checks_nomme_le_droit_manquant(
    real_pg_db_sans_privilege: str, tmp_path, capsys
) -> None:
    """`fixtures:load --run --no-fk-checks` s'arrête en expliquant.

    Mesuré avant le correctif : la commande n'explose pas en trace, elle
    attrape et rend « Erreur en chargeant (chargement annulé) : droit refusé
    pour initialiser le paramètre ... ». Elle échoue donc proprement, mais sans
    qualifier la cause ni dire quoi faire, et le texte du serveur est traduit.

    La sortie lue couvre stdout **et** stderr : la commande rapporte ses échecs
    sur stderr, et ne lire que stdout ferait passer le test pour la mauvaise
    raison.
    """
    from forge_mvc_fixtures.cli.load import load_fixtures

    _projet_avec_une_fixture(tmp_path)

    code = load_fixtures(tmp_path, run=True, force=True, env="test", no_fk_checks=True)

    capture = capsys.readouterr()
    sortie = capture.out + capture.err
    assert code != 0, "la commande doit échouer, pas charger à moitié"
    assert "droit" in sortie.lower() or "privilège" in sortie.lower(), sortie
    assert "session_replication_role" in sortie, (
        "le message doit nommer le levier refusé, sinon il n'oriente pas"
    )


def test_purge_nomme_le_droit_manquant(
    real_pg_db_sans_privilege: str, tmp_path, capsys
) -> None:
    """`fixtures:purge` emprunte le même chemin, et doit dire la même chose.

    Le premier correctif d'`error_page` n'avait réparé qu'un jumeau sur deux ;
    la leçon est reprise ici, les deux commandes étant vérifiées.
    """
    from forge_mvc_fixtures.cli.purge import purge_fixtures

    _projet_avec_une_fixture(tmp_path)

    code = purge_fixtures(tmp_path, run=True, force=True, env="test")

    capture = capsys.readouterr()
    sortie = capture.out + capture.err
    assert code != 0
    assert "droit" in sortie.lower() or "privilège" in sortie.lower(), sortie
