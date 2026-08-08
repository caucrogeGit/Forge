# pyright: strict
"""Table du registre anti-rejeu TOTP, décrite une fois pour les quatre backends.

Cette table n'est **pas** requise pour utiliser `forge-mvc-mfa`.
Le paquet reste une bibliothèque, sans persistance : les facteurs appartiennent
à l'application, et le registre anti-rejeu vit par défaut en mémoire.
Elle ne sert qu'aux projets qui installent
:class:`~forge_mvc_mfa.replay_store_db.DbTotpReplayStore` pour partager le
registre entre plusieurs processus.

`forge mfa:init` rend cette description pour le backend installé et écrit le SQL
dans `mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["TOTP_REPLAY", "TOTP_REPLAY_TABLE_NAME", "MIGRATIONS"]

#: Nom de la table du registre.
TOTP_REPLAY_TABLE_NAME = "mfa_totp_replay"

TOTP_REPLAY = TableDefinition(
    name=TOTP_REPLAY_TABLE_NAME,
    columns=[
        # Une ligne par facteur, pas une par code consommé. Le contrat refuse
        # toute fenêtre antérieure ou égale à la dernière vue, donc retenir la
        # dernière suffit et borne la table au nombre de facteurs actifs.
        #
        # `identity_ref` et non `integer` : la colonne référence une clé
        # d'identité applicative, dont le type de stockage varie par backend
        # (FK-IDENTITY-STORAGE-TYPE-001). Aucune clé étrangère n'est déclarée,
        # la table des facteurs appartenant à l'application et Forge ne pouvant
        # pas en présumer le nom.
        Column("factor_id", "identity_ref"),
        Column("last_step", "big_integer"),
        Column("updated_at", "datetime", default_now=True),
    ],
    primary_key=["factor_id"],
    # La purge balaie par `last_step`, jamais par une date : comparer des
    # numéros de fenêtre évite toute arithmétique de date non portable, dont
    # l'audit `OPTIN-DML-DIALECT-001` a montré le coût.
    indexes=[Index("idx_mfa_totp_replay_step", "last_step")],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260808120000_create_mfa_totp_replay.sql", TOTP_REPLAY),
]
