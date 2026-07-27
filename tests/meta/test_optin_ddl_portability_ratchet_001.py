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
NON_PORTABLE_YET = {
    "packages/forge-mvc-audit/forge_mvc_audit/migrations/20260626130000_create_audit_log.sql",
    "packages/forge-mvc-images/forge_mvc_images/migrations/20260710120000_create_media.sql",
    "packages/forge-mvc-iot/forge_mvc_iot/migrations/20260528120000_create_iot_events.sql",
    "packages/forge-mvc-jobs/forge_mvc_jobs/migrations/20260626140000_create_jobs.sql",
    "packages/forge-mvc-mfa/sql/auth_mfa_factors.sql",
    "packages/forge-mvc-mfa/sql/auth_mfa_recovery_codes.sql",
    "packages/forge-mvc-notifications/forge_mvc_notifications/migrations/20260626150000_create_notifications.sql",
    "packages/forge-mvc-rbac/sql/rbac.sql",
    "packages/forge-mvc-rbac/sql/user_roles.sql",
    "packages/forge-mvc-sessions-db/forge_mvc_sessions_db/migrations/20260710130000_create_forge_sessions.sql",
    "packages/forge-mvc-settings/forge_mvc_settings/migrations/20260626120000_create_app_settings.sql",
    "packages/forge-mvc-video/forge_mvc_video/migrations/20260601120000_create_videos.sql",
}


def _shipped_sql_files() -> list[Path]:
    return [
        path for path in sorted(PACKAGES.rglob("*.sql"))
        if "/build/" not in path.as_posix()
    ]


def _markers_in(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8").upper()
    return sorted(marker for marker in MARIADB_ONLY if marker in content)


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_le_scan_trouve_bien_du_sql_a_auditer() -> None:
    """Sans ce contrôle, un scan cassé rendrait le cliquet vert par accident."""
    assert len(_shipped_sql_files()) >= 10


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
