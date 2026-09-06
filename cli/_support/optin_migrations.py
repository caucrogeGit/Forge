# pyright: strict
"""Provisioning partagé des opt-ins BDD (CORE-OPTIN-INIT-HELPER-001, ADR-071).

Les opt-ins adossés à la base (audit, settings, jobs, notifications, sessions-db,
images, video, iot) exposent tous une commande ``<optin>:init`` qui copie leurs
migrations SQL embarquées (``<package>/migrations/*.sql``) vers ``mvc/migrations/``
du projet, sans exécuter aucun SQL (charte §7 : Forge génère, l'opérateur
applique). La logique était dupliquée à l'identique dans chaque paquet ; elle est
centralisée ici. Chaque ``cli/init.py`` d'opt-in n'est plus qu'un mince adaptateur
qui fournit son nom de paquet et son libellé.

Idempotent, jamais d'écrasement silencieux : un fichier déjà présent au contenu
identique est signalé OK, un fichier différent provoque un WARN sans modification.

Deux sources de migration cohabitent le temps du chantier
`OPTIN-DDL-DIALECTAL` :

- **rendu dialectal** (cible) : le paquet expose un module ``tables`` avec une
  liste ``MIGRATIONS`` de ``(nom de fichier, déclaration)``, où une déclaration
  est une ``TableDefinition`` à créer ou un ``AddColumn`` à ajouter à une table
  déjà provisionnée. Le SQL est rendu pour le backend actif via
  ``core.database.table_ddl`` ;
- **fichier figé** (héritage) : le paquet livre des ``.sql`` sous
  ``<package>/migrations/``, copiés tels quels. L'audit
  ``OPTIN-DDL-DIALECT-AUDIT-001`` a mesuré que ces fichiers ne s'exécutent que
  sur MariaDB ; ils sont repris paquet par paquet, et le cliquet
  ``tests/meta/test_optin_ddl_portability_ratchet_001.py`` empêche la liste de
  grandir.

Le SQL rendu reste **visible** : il est écrit dans ``mvc/migrations/``, relu
puis appliqué par ``forge migration:apply`` (charte §7, ADR-071).
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from importlib import import_module, resources
from pathlib import Path

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"


def _rendered_header(package: str, filename: str, backend_name: str) -> str:
    return (
        f"-- Migration Forge rendue pour le backend « {backend_name} ».\n"
        f"-- Source : {package} (déclaration : {package}.tables).\n"
        "--\n"
        "-- Ce fichier a été GÉNÉRÉ par `forge <opt-in>:init` à partir d'une\n"
        "-- description de table unique, rendue par le dialecte du backend\n"
        "-- installé. Relisez-le, puis appliquez-le : forge migration:apply\n"
        "--\n"
        "-- Changer de backend en cours de projet suppose de reprovisionner :\n"
        "-- le SQL rendu diffère, et `migration:apply` refuse une migration\n"
        "-- déjà appliquée dont le contenu a changé.\n"
        "\n"
    )


def _rendered_migrations(package: str) -> "list[tuple[str, bytes]] | None":
    """Rend les migrations déclarées par ``<package>.tables``, si ce module existe.

    Retourne ``None`` quand le paquet n'a pas encore été repris et livre encore
    des ``.sql`` figés.
    """
    try:
        module = import_module(f"{package}.tables")
    except ModuleNotFoundError:
        return None

    declarations = getattr(module, "MIGRATIONS", None)
    if not declarations:
        return None

    from core.database.backend import get_backend
    from core.database.table_ddl import AddColumn, render_add_column, render_create_table

    backend = get_backend()

    # Les colonnes qu'une migration ULTÉRIEURE ajoutera sont retirées de la
    # création (`OPTIN-MIGRATIONS-FRESH-INSTALL-001`).
    #
    # La déclaration de table évolue avec le paquet : elle porte aujourd'hui
    # toutes ses colonnes. La rendre telle quelle dans la migration de création
    # donnait, sur une base NEUVE, une table déjà complète, puis un
    # `ALTER TABLE ADD COLUMN` sur une colonne existante. Mesuré :
    # `duplicate column name: priority`, et `forge migration:apply` s'arrête là.
    #
    # Trois opt-ins étaient dans ce cas, et aucun n'était provisionnable sur un
    # projet neuf : sessions-db, jobs et notifications.
    #
    # Retirer ces colonnes de la création rend la suite cohérente pour tout le
    # monde. Un projet neuf joue création puis ajouts, un projet déjà
    # provisionné ne rejoue pas la création et joue les seuls ajouts, et les
    # deux aboutissent à la même table.
    ajoutees = {
        d.column_name for _f, d in declarations if isinstance(d, AddColumn)
    }
    index_ajoutes = {
        nom
        for _f, d in declarations
        if isinstance(d, AddColumn)
        for nom in (d.index_names or ())
    }

    out: list[tuple[str, bytes]] = []
    for filename, declaration in declarations:
        # Une déclaration est soit une table à créer, soit une colonne à ajouter
        # à une table déjà provisionnée (SESSIONS-DELETE-FOR-USER-001). Sans le
        # second cas, un opt-in ne pouvait pas faire évoluer son schéma sans
        # casser les projets existants.
        if isinstance(declaration, AddColumn):
            statements = render_add_column(
                declaration.table,
                declaration.column_name,
                backend.dialect,
                declaration.index_names,
                declaration.unique_nullable_index,
            )
        else:
            statements = render_create_table(
                _sans_colonnes_ajoutees(declaration, ajoutees, index_ajoutes),
                backend.dialect,
            )
        body = _rendered_header(package, filename, backend.name) + "\n".join(statements) + "\n"
        out.append((filename, body.encode("utf-8")))
    return out


def _sans_colonnes_ajoutees(
    table: Any, colonnes: "set[str]", index: "set[str]"
) -> Any:
    """Table privée des colonnes qu'une migration ultérieure ajoutera.

    Rend la table telle quelle quand il n'y a rien à retirer : la copie n'a
    alors aucune raison d'exister, et l'égalité des objets reste vraie pour les
    paquets qui n'ont qu'une création.
    """
    import dataclasses

    if not colonnes:
        return table

    def _index_survivant(declaration: Any) -> bool:
        # Un index nommé par l'ajout lui appartient. Un index qui PORTE sur une
        # colonne retirée ne peut pas être créé ici non plus : la table ne
        # l'aurait pas encore. Mesuré : « no such column: user_id » à la
        # création, une fois la colonne écartée.
        if declaration.name in index:
            return False
        return not (set(declaration.columns) & colonnes)

    return dataclasses.replace(
        table,
        columns=[c for c in table.columns if c.name not in colonnes],
        indexes=[i for i in table.indexes if _index_survivant(i)],
    )


def iter_migration_resources(package: str) -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration de ``package``.

    Rend les migrations déclarées (``<package>.tables``) pour le backend actif ;
    à défaut, copie les ``.sql`` figés de ``<package>/migrations``.
    """
    rendered = _rendered_migrations(package)
    if rendered is not None:
        yield from rendered
        return

    anchor = resources.files(package) / "migrations"
    for entry in sorted(anchor.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            yield entry.name, entry.read_bytes()


def init_optin_migrations(package: str, label: str, project_root: Path) -> int:
    """Copie les migrations SQL de ``package`` vers ``<project_root>/mvc/migrations/``.

    ``label`` nomme l'opt-in dans les messages (« Audit », « Sessions »...).
    Renvoie 0 (succès, idempotent inclus) ou 1 si ``mvc/`` est absent (le dossier
    courant n'est pas un projet Forge).
    """
    mvc_dir = project_root / "mvc"
    if not mvc_dir.is_dir():
        print(f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge.")
        print("Conseil : lance cette commande à la racine du projet (dossier mvc/ attendu).")
        return 1

    target_dir = mvc_dir / "migrations"
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        print(f"{STATUS_INFO} Dossier mvc/migrations/ créé.")

    copied: list[str] = []
    skipped_identical: list[str] = []
    skipped_different: list[str] = []

    try:
        migrations = list(iter_migration_resources(package))
    except Exception as error:  # noqa: BLE001 — message d'opérateur, pas de trace
        # Une migration rendue exige un backend résolu (ADR-054). Sans lui, on
        # explique au lieu de dérouler une pile d'appels.
        print(f"{STATUS_ERROR} Impossible de préparer la migration {label} : {error}")
        print("Conseil : installe un backend BDD (un seul par projet), par exemple")
        print("          pip install forge-mvc-mariadb")
        return 1

    for name, content in migrations:
        target = target_dir / name
        if target.exists():
            if target.read_bytes() == content:
                skipped_identical.append(name)
            else:
                skipped_different.append(name)
            continue
        target.write_bytes(content)
        copied.append(name)

    for name in copied:
        print(f"{STATUS_OK} Migration {label} copiée : mvc/migrations/{name}")
    for name in skipped_identical:
        print(f"{STATUS_OK} Migration {label} déjà présente (identique) : mvc/migrations/{name}")
    for name in skipped_different:
        print(f"{STATUS_WARN} mvc/migrations/{name} existe et diffère, aucune modification.")

    if copied or skipped_identical:
        print()
        print(f"{STATUS_INFO} Lance maintenant : forge migration:apply")

    return 0
