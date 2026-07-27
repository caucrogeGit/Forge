"""OPTIN-DDL-GUARD-RATCHET-001 — cliquet de portabilité du DDL des opt-ins.

L'audit `OPTIN-DDL-DIALECT-AUDIT-001` (2026-07-27) a mesuré sur quatre
serveurs réels que les 12 fichiers SQL livrés par 10 opt-ins étaient
inexécutables ailleurs que sur MariaDB, alors que l'ADR-084 déclare les quatre
backends au niveau plein.

Ce garde-fou est un **cliquet**, sur le modèle de la strictness par paliers de
l'ADR-036 : la liste des contrevenants connus ne peut que **diminuer**.

- un fichier SQL **hors liste** qui emploie une construction propre à MariaDB
  fait échouer le test : aucun nouvel opt-in ne peut réintroduire le défaut ;
- un fichier **dans la liste** qui n'en emploie plus fait aussi échouer le
  test, avec le message « retirez-le de la liste » : le cliquet se resserre au
  fil des corrections et ne peut pas se relâcher en silence.

Le rendu portable à utiliser est `core.database.table_ddl.render_create_table`
(`DB-TABLE-DDL-RENDERER-001`), qui passe par le contrat `Dialect`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES = PROJECT_ROOT / "packages"

# Constructions propres à MariaDB/MySQL. Chacune est la cause mesurée d'au
# moins un échec dans l'audit, et chacune a son équivalent au contrat Dialect.
MARIADB_ONLY = {
    "AUTO_INCREMENT": "Dialect.identity_type() / auto_increment_column_ddl()",
    "UNSIGNED": "Dialect.identity_type() / identity_storage_type()",
    "ENGINE=": "Dialect.table_suffix() / collated_table_suffix()",
    "ON UPDATE CURRENT_TIMESTAMP": "Dialect.timestamp_default_clause(on_update=True)",
    "LONGTEXT": "Dialect.simple_type('text')",
}

# ── LE CLIQUET ────────────────────────────────────────────────────────────────
# Fichiers encore non portables au 2026-07-27. Cette liste ne doit JAMAIS
# grandir. Retirez une entrée quand le paquet correspondant est passé au rendu
# dialectal ; n'en ajoutez aucune.
# Tous les fichiers `.sql` figés livrés par un paquet ont été convertis au
# 2026-07-27 : sessions-db, rbac et mfa, puis audit, images, iot, jobs,
# notifications, settings et video. Aucun ne subsiste.
#
# Restent des DDL écrits en dur dans du **Python**, que le scan initial de
# l'audit avait manqués parce qu'il ne regardait que le `.sql` : quatre
# constantes `CREATE_TABLE_SQL` doublonnant une migration désormais dialectale,
# et cinq autres emplacements dans des paquets que l'audit n'avait pas
# identifiés (dont `mail` et `stats`).
NON_PORTABLE_YET = {
    # Constantes CREATE_TABLE_SQL : doublon de la migration, API publique
    # documentée (18 pages) — conversion en ticket dédié.
    "packages/forge-mvc-audit/forge_mvc_audit/store.py",
    "packages/forge-mvc-jobs/forge_mvc_jobs/queue.py",
    "packages/forge-mvc-notifications/forge_mvc_notifications/store.py",
    "packages/forge-mvc-settings/forge_mvc_settings/store.py",
    # Non repérés par l'audit initial : DDL en Python, pas en .sql.
    "packages/forge-mvc-entities/forge_mvc_entities/db_init.py",
    "packages/forge-mvc-entities/forge_mvc_entities/migrations.py",
    "packages/forge-mvc-iot/forge_mvc_iot/cli/doctor.py",
    "packages/forge-mvc-mail/forge_mvc_mail/cli.py",
    "packages/forge-mvc-stats/forge_mvc_stats/schema.py",
}


def _shipped_sql_files() -> list[Path]:
    """Fichiers SQL et modules Python livrés par un paquet, susceptibles de DDL.

    Le scan couvre le **Python** en plus du `.sql` : supprimer un fichier figé
    tout en laissant la même table écrite en dur dans une constante Python
    rendrait le cliquet vert sans rien avoir corrigé.

    Sont exclus : les backends BDD, dont le dialecte MariaDB émet légitimement
    ces constructions puisque c'est son travail ; et les tests, qui doivent
    pouvoir citer ces chaînes pour les vérifier.
    """
    out = [
        path for path in sorted(PACKAGES.rglob("*.sql"))
        if "/build/" not in path.as_posix()
    ]
    for path in sorted(PACKAGES.rglob("*.py")):
        posix = path.as_posix()
        if "/build/" in posix or "/tests/" in posix or "/dialect.py" in posix:
            continue
        if "/forge-mvc-mariadb/" in posix or "/forge-mvc-sqlite/" in posix:
            continue
        if "/forge-mvc-postgres/" in posix or "/forge-mvc-mssql/" in posix:
            continue
        if "CREATE TABLE" not in path.read_text(encoding="utf-8"):
            continue
        out.append(path)
    return out


def _markers_in(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8").upper()
    return sorted(marker for marker in MARIADB_ONLY if marker in content)


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_le_scan_trouve_bien_du_sql_a_auditer() -> None:
    """Sans ce contrôle, un scan cassé rendrait le cliquet vert par accident.

    Le seuil suit la taille du cliquet : tant qu'il reste des fichiers listés,
    le scan doit au moins les retrouver. Quand le cliquet sera vide, ce contrôle
    deviendra sans objet et pourra disparaître avec lui.
    """
    assert len(_shipped_sql_files()) >= len(NON_PORTABLE_YET)


def test_aucun_nouveau_fichier_non_portable() -> None:
    """Le cliquet ne grandit pas : un opt-in neuf doit être portable d'emblée."""
    offenders: list[str] = []
    for path in _shipped_sql_files():
        rel = _relative(path)
        if rel in NON_PORTABLE_YET:
            continue
        markers = _markers_in(path)
        if markers:
            equivalents = "; ".join(f"{m} -> {MARIADB_ONLY[m]}" for m in markers)
            offenders.append(f"{rel} : {equivalents}")
    assert not offenders, (
        "Du SQL propre a MariaDB est livre par un paquet hors cliquet.\n"
        "Employez core.database.table_ddl.render_create_table, qui passe par le "
        "contrat Dialect (DB-TABLE-DDL-RENDERER-001).\n  - "
        + "\n  - ".join(offenders)
    )


@pytest.mark.parametrize("relative_path", sorted(NON_PORTABLE_YET))
def test_le_cliquet_se_resserre(relative_path: str) -> None:
    """Une entrée corrigée ou disparue doit être retirée de la liste.

    C'est ce qui empêche le cliquet de se relâcher : on ne peut pas oublier de
    le mettre à jour, le test le réclame.
    """
    path = PROJECT_ROOT / relative_path
    assert path.is_file(), (
        f"{relative_path} n'existe plus : retirez-le de NON_PORTABLE_YET."
    )
    assert _markers_in(path), (
        f"{relative_path} n'emploie plus de construction propre a MariaDB : "
        "retirez-le de NON_PORTABLE_YET (le cliquet se resserre)."
    )
