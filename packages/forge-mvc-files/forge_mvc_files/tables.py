# pyright: strict
"""Registre des fichiers écrits par l'opt-in (ADR-094).

`forge-mvc-files` écrivait des fichiers sans garder trace de ce qu'il avait
écrit, l'ADR-020 ayant exclu tout état de son périmètre. Une conséquence
n'avait pas été mesurée : sans registre, aucun quota n'est calculable, aucun
orphelin n'est repérable, et le nom d'origine ne survit pas au mode UUID, qui
l'efface du chemin par sécurité.

L'ADR-094 amende ce point, et ce point seul. La table porte ce que le
**stockage** sait d'un fichier, jamais une notion métier : le rôle, la position
et le texte alternatif restent dans la table `media` de `forge-mvc-images`, où
une galerie en a besoin.

`forge files:init` rend cette description pour le backend installé et écrit le
SQL dans `mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["FILES", "FILES_TABLE_NAME", "MIGRATIONS"]

#: Nom de la table du registre.
FILES_TABLE_NAME = "forge_files"

FILES = TableDefinition(
    name=FILES_TABLE_NAME,
    columns=[
        Column("id", "identity"),
        # Chemin relatif sous la racine d'upload, tel que `save_upload` le rend.
        # Unique : deux lignes pour un même fichier rendraient tout quota faux.
        Column("path", "string", length=500, unique=True),
        # Le mode UUID efface le nom d'origine du chemin, par sécurité. Sans
        # cette colonne, il est perdu pour de bon.
        Column("original_name", "string", length=255),
        Column("mime_type", "string", length=120, nullable=True),
        Column("size_bytes", "big_integer"),
        # Propriétaire déclaré par l'application : une nature et un identifiant,
        # libres. `forge-mvc-files` ne sait pas ce qu'est un utilisateur et ne
        # cherche pas à le savoir (ADR-094). Nullable : un fichier peut n'avoir
        # aucun propriétaire, et les deux colonnes vont de pair.
        Column("owner_kind", "string", length=64, nullable=True),
        Column("owner_id", "string", length=191, nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    indexes=[
        # Le quota compte par propriétaire, d'où l'index sur le couple.
        Index("idx_forge_files_owner", ("owner_kind", "owner_id")),
        Index("idx_forge_files_created", "created_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260901100000_create_forge_files.sql", FILES),
]
