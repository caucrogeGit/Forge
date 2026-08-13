"""Le script de provisionnement PostgreSQL s'exécute réellement (DB-INIT-PROVISION-REAL-001).

`forge db:init` est la **première** commande d'un projet Forge. Elle rend un
script SQL que l'opérateur colle dans une session d'administration (ADR-067).
Ce script n'avait jamais été exécuté : les tests comparaient son texte à un
texte attendu.

C'est le pire endroit pour une vérification par comparaison de chaînes. Un
script de provisionnement invalide bloque un projet **avant** qu'il existe,
sans rattrapage possible et sans aucun autre test pour le rattraper : rien ne
tourne encore.

Le script est écrit pour `psql`, dont il emploie la méta-commande `\\connect`.
Il est donc exercé par `psql`, comme un opérateur le ferait, et non par le
pilote, qui ne saurait pas l'interpréter.

Ce test crée de vrais rôles et une vraie base, sous des noms jetables préfixés
`forge_initprobe_`, et les supprime dans tous les cas.
"""
from __future__ import annotations

import os
import shutil
import subprocess

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.db_init import ProvisioningEnv, generate_provisioning_sql_postgres

pytestmark = pytest.mark.db_pg

#: Préfixe reconnaissable : si une purge échoue, l'objet reste identifiable.
_PREFIXE = "forge_initprobe"

_BASE = f"{_PREFIXE}_base"
_ADMIN = f"{_PREFIXE}_admin"
_APP = f"{_PREFIXE}_app"


def _psql(sql: str, *, base: str = "postgres") -> subprocess.CompletedProcess[str]:
    """Exécute du SQL par `psql`, seul capable des méta-commandes du script."""
    env = dict(os.environ)
    env["PGPASSWORD"] = os.environ.get("FORGE_TEST_PG_PASSWORD", "forge_test_pg")
    return subprocess.run(
        [
            "psql",
            "-h", os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"),
            "-p", os.environ.get("FORGE_TEST_PG_PORT", "5432"),
            "-U", os.environ.get("FORGE_TEST_PG_USER", "postgres"),
            "-d", base,
            "-v", "ON_ERROR_STOP=1",
            "-X",
            "-c", sql,
        ] if "\\connect" not in sql else [
            "psql",
            "-h", os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"),
            "-p", os.environ.get("FORGE_TEST_PG_PORT", "5432"),
            "-U", os.environ.get("FORGE_TEST_PG_USER", "postgres"),
            "-d", base,
            "-v", "ON_ERROR_STOP=1",
            "-X",
            "-f", "-",
        ],
        input=sql if "\\connect" in sql else None,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def _scalaire(sql: str, *, base: str = "postgres") -> str:
    """Valeur unique rendue par `psql`, sans en-tête ni alignement."""
    env = dict(os.environ)
    env["PGPASSWORD"] = os.environ.get("FORGE_TEST_PG_PASSWORD", "forge_test_pg")
    resultat = subprocess.run(
        [
            "psql",
            "-h", os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"),
            "-p", os.environ.get("FORGE_TEST_PG_PORT", "5432"),
            "-U", os.environ.get("FORGE_TEST_PG_USER", "postgres"),
            "-d", base,
            "-tAX",
            "-v", "ON_ERROR_STOP=1",
            "-c", sql,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert resultat.returncode == 0, resultat.stderr
    return resultat.stdout.strip()


def _purger() -> None:
    """Supprime base et rôles, quel que soit l'état laissé par le test."""
    _psql(f"DROP DATABASE IF EXISTS {_BASE} WITH (FORCE);")
    for role in (_APP, _ADMIN):
        _psql(f"DROP ROLE IF EXISTS {role};")


@pytest.fixture
def terrain():
    if shutil.which("psql") is None:
        pytest.skip("psql absent : le script de provisionnement s'exécute par psql")
    _purger()
    try:
        yield
    finally:
        _purger()


def _migrations_ddl() -> str:
    """La DDL du registre, telle que la commande la fournit au rendu.

    La passer vide produit un script qui accorde des droits sur une table
    inexistante. Le contrat de la fonction ne l'interdit pas, ce qui mérite
    d'être noté : c'est un paramètre dont l'omission n'échoue qu'au serveur.
    """
    from forge_mvc_postgres.dialect import PostgreSQLDialect

    return PostgreSQLDialect().forge_migrations_ddl()


def _config() -> ProvisioningEnv:
    return ProvisioningEnv(
        db_name=_BASE,
        admin_login=_ADMIN,
        admin_password="Sonde#Admin#2026",
        app_login=_APP,
        app_password="Sonde#App#2026",
        app_privileges=["SELECT", "INSERT", "UPDATE", "DELETE"],
        # Propres à MariaDB, ignorés par le rendu PostgreSQL, mais exigés par
        # le contrat commun de `ProvisioningEnv`.
        db_charset="utf8mb4",
        db_collation="utf8mb4_general_ci",
        host=os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"),
    )


def test_le_script_de_provisionnement_s_execute_sans_erreur(terrain: None) -> None:
    """LE test : ce que `forge db:init` rend doit être accepté par le serveur.

    Une erreur ici bloque un projet avant sa première ligne de code, et aucun
    autre test ne peut la rattraper puisque rien ne tourne encore.
    """
    script = generate_provisioning_sql_postgres(_config(), _migrations_ddl())

    resultat = _psql(script)

    assert resultat.returncode == 0, (
        "le script rendu par `forge db:init` est refusé par PostgreSQL :\n"
        f"{resultat.stderr}"
    )


def test_le_script_cree_bien_ce_qu_il_annonce(terrain: None) -> None:
    """Un script qui s'exécute sans rien créer passerait le test précédent.

    C'est le mode de défaillance propre aux scripts idempotents : les erreurs
    y sont tolérées par construction, et le succès ne prouve donc rien sur le
    résultat.
    """
    script = generate_provisioning_sql_postgres(_config(), _migrations_ddl())
    assert _psql(script).returncode == 0

    roles = _psql(
        f"SELECT rolname FROM pg_roles WHERE rolname LIKE '{_PREFIXE}%' ORDER BY rolname;"
    )
    bases = _psql(f"SELECT datname FROM pg_database WHERE datname = '{_BASE}';")

    assert _ADMIN in roles.stdout, f"le rôle d'administration manque :\n{roles.stdout}"
    assert _APP in roles.stdout, f"le rôle applicatif manque :\n{roles.stdout}"
    assert _BASE in bases.stdout, f"la base du projet manque :\n{bases.stdout}"


def test_le_compte_applicatif_n_a_que_le_dml(terrain: None) -> None:
    """La propriété de sécurité du provisionnement, jamais vérifiée en exécution.

    Le compte applicatif tourne en production. Qu'il puisse créer ou supprimer
    des tables annulerait la séparation des trois niveaux de l'ADR-067, et cela
    ne se voit pas sur le texte du script.
    """
    script = generate_provisioning_sql_postgres(_config(), _migrations_ddl())
    assert _psql(script).returncode == 0

    # `has_table_privilege` répond sur les droits **effectifs**, ce que le texte
    # du script ne dit pas. Le registre des migrations est la table de contrôle :
    # le compte applicatif doit la lire et l'écrire, jamais la redéfinir.
    accorde = {
        droit: _scalaire(
            f"SELECT has_table_privilege('{_APP}', 'forge_migrations', '{droit}');",
            base=_BASE,
        )
        for droit in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES")
    }

    for droit in ("SELECT", "INSERT", "UPDATE", "DELETE"):
        assert accorde[droit] == "t", (
            f"le compte applicatif n'a pas {droit}, il ne pourra pas tourner"
        )

    interdits = [droit for droit in ("TRUNCATE", "REFERENCES") if accorde[droit] == "t"]
    assert not interdits, (
        f"le compte applicatif dépasse le DML : {', '.join(interdits)}. "
        "La séparation des trois niveaux de l'ADR-067 ne tient plus."
    )


def test_le_compte_applicatif_ne_peut_pas_creer_de_table(terrain: None) -> None:
    """La preuve par l'échec : le compte applicatif tente et doit être refusé.

    Vérifier un catalogue de droits reste une lecture. Ici le rôle agit, et
    c'est le serveur qui répond. Un test de droit qui ne serait vrai que par
    l'effet d'un réglage par défaut du serveur passerait sans rien garder.
    """
    script = generate_provisioning_sql_postgres(_config(), _migrations_ddl())
    assert _psql(script).returncode == 0

    tentative = _psql(
        f"SET ROLE {_APP}; CREATE TABLE tentative_interdite (id integer);",
        base=_BASE,
    )

    assert tentative.returncode != 0, (
        "le compte applicatif a pu créer une table : il ne se limite pas au DML"
    )
    assert "droit" in tentative.stderr.lower() or "permission" in tentative.stderr.lower(), (
        f"refus attendu pour cause de droits, obtenu :\n{tentative.stderr}"
    )
