"""OPTIN-DDL-GUARD-RATCHET-001 — cliquet de portabilité du DDL des opt-ins.

L'audit `OPTIN-DDL-DIALECT-AUDIT-001` (2026-07-27) a mesuré sur quatre
serveurs réels que les 12 fichiers SQL livrés par 10 opt-ins étaient
inexécutables ailleurs que sur MariaDB, alors que l'ADR-084 déclare les quatre
backends au niveau plein.

Ce garde-fou était un **cliquet**, sur le modèle de la strictness par paliers
de l'ADR-036 : la liste des contrevenants ne pouvait que diminuer, entrée par
entrée, au fil des conversions.

**Le cliquet est arrivé au bout : `NON_PORTABLE_YET` est vide.** Le garde-fou
devient donc un invariant absolu — aucun paquet ne livre de SQL propre à
MariaDB, ni en `.sql`, ni en dur dans un module Python.

La liste est conservée, vide, plutôt que supprimée : elle documente le
mécanisme et reste le point d'entrée si une exception temporaire devait un
jour être tolérée. Les deux sens du contrôle restent actifs, donc une entrée
ajoutée sans être justifiée échouerait aussitôt qu'elle serait corrigée.

Le rendu portable à utiliser est `core.database.table_ddl.render_create_table`
(`DB-TABLE-DDL-RENDERER-001`), qui passe par le contrat `Dialect`.
"""
from __future__ import annotations

import ast
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
    # Constantes CREATE_TABLE_SQL : les quatre ont été SUPPRIMÉES le 2026-07-27
    # (OPTIN-DDL-CONSTANTS-001). Elles doublonnaient la migration et offraient
    # une seconde façon officielle de créer la même table, contre le principe 11.
    # La source unique est désormais la déclaration `<paquet>.tables`, rendue par
    # `<opt-in>:init` puis appliquée par `forge migration:apply`.
    # forge-mvc-entities : les deux entrées RETIRÉES le 2026-07-27
    # (OPTIN-DDL-ENTITIES-001). db_init.py dupliquait caractère pour
    # caractère `Dialect.forge_migrations_ddl()`, qu'il appelle désormais ;
    # migrations.py posait AUTO_INCREMENT en dur dans le chemin de diff et
    # montrait un exemple MariaDB dans le gabarit de migration.
    # Non repérés par l'audit initial : DDL en Python, pas en .sql.
    # forge-mvc-iot/cli/doctor.py : RETIRÉ le 2026-07-27
    # (OPTIN-DDL-IOT-DOCTOR-001). Ses types MariaDB en dur étaient un
    # CONTRAT de colonnes attendu, pas du DDL : le controle passe désormais
    # par Dialect.introspect_columns et compare des familles de types.
    # forge-mvc-mail et forge-mvc-stats : RETIRÉS le 2026-07-27
    # (OPTIN-DDL-MAIL-STATS-001). Ils déclarent désormais leur table et le DDL
    # est rendu par le dialecte. LE CLIQUET EST VIDE : plus aucun paquet ne
    # livre de SQL propre à MariaDB.
}


def _shipped_sql_files() -> list[Path]:
    """Fichiers SQL et modules Python livrés par un paquet, susceptibles de DDL.

    Le scan couvre le **Python** en plus du `.sql` : supprimer un fichier figé
    tout en laissant la même table écrite en dur dans une constante Python
    rendrait le garde-fou vert sans rien avoir corrigé.

Le scan se limite aux modules contenant `CREATE TABLE`, c'est-à-dire à
    l'**émission de DDL**, qui est l'objet de ce garde-fou.

    Élargir à tous les modules révèle une autre famille de défaut, distincte :
    du code qui **branche sur des noms de types MariaDB** (`LONGTEXT`,
    `UNSIGNED`) pour décider d'un comportement, par exemple choisir un widget
    de formulaire. Sur PostgreSQL ces noms n'apparaissent jamais, donc la
    branche ne se déclenche pas. Cinq modules sont concernés
    (`entities/crud/utils.py`, `make_crud.py`, `relations.py`,
    `validation.py`, `iot/cli/doctor.py`). Cela relève d'un audit propre, pas
    d'un élargissement discret de celui-ci.

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
    """Constructions propres à MariaDB trouvées dans `path`.

    Deux régimes, parce que les deux formats ne se prêtent pas au même
    contrôle :

    - **`.sql`** : tout le texte, sans distinction de casse. Un fichier SQL
      n'a pas d'autre contenu que du SQL.
    - **`.py`** : seules les **chaînes littérales**, et à la casse exacte.
      Deux faux positifs sont ainsi évités. D'abord les identifiants : le nom
      de champ `auto_increment` est du Python parfaitement portable, il
      deviendrait `AUTO_INCREMENT` si l'on passait le fichier en majuscules.
      Ensuite les clés de dictionnaire et messages : `field["auto_increment"]`
      est une chaîne, mais en minuscules. Le SQL de ce dépôt écrit ses
      mots-clés en majuscules, la casse suffit donc à discriminer.

    Les docstrings sont incluses, et c'est voulu : un exemple SQL montré à
    l'auteur d'un projet doit être portable lui aussi.
    """
    content = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        haystack = content.upper()
        return sorted(marker for marker in MARIADB_ONLY if marker in haystack)

    try:
        tree = ast.parse(content)
    except SyntaxError:  # pragma: no cover - un module cassé casse déjà ailleurs
        return sorted(marker for marker in MARIADB_ONLY if marker in content)

    haystack = "\n".join(
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    return sorted(marker for marker in MARIADB_ONLY if marker in haystack)


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_le_scan_trouve_bien_du_sql_a_auditer() -> None:
    """Sans ce contrôle, un scan cassé rendrait le garde-fou vert par accident.

    Le cliquet étant vide, le seuil ne peut plus suivre sa taille : on vérifie
    donc que le scan trouve toujours des modules porteurs de `CREATE TABLE`.
    S'il n'en trouvait plus aucun, ce serait le scan qui serait cassé, pas le
    dépôt qui serait devenu parfait.
    """
    scanned = _shipped_sql_files()
    assert len(scanned) >= 2, (
        f"Le scan ne couvre que {len(scanned)} fichiers : verifier "
        "_shipped_sql_files() avant de conclure que tout est portable."
    )


def test_aucun_fichier_non_portable() -> None:
    """Aucun paquet ne livre de SQL propre à MariaDB. Invariant absolu."""
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
