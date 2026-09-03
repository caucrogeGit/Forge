# pyright: strict
"""Table du store de session, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait auparavant, et qui portait
lui-même l'aveu de sa limite : « DDL MariaDB. Adaptez les types au backend
actif si nécessaire. » L'adaptation est désormais faite par le rendu dialectal
(`core.database.table_ddl`), pas reportée sur l'auteur du projet.

`forge sessions:init` rend cette description pour le backend installé et écrit
le SQL obtenu dans `mvc/migrations/`, où il reste relisible avant application
(principe 5, ADR-071 inchangé).

Horodatages : Python reste l'unique autorité (UTC). Aucun `DEFAULT
CURRENT_TIMESTAMP` ni mise à jour automatique, pour ne pas installer une
seconde horloge côté SGBD (retour terrain 016 F37).
La colonne `version` sert la concurrence optimiste du store, sous la garde
`WHERE version = ?` (F36).
"""
from __future__ import annotations

from core.database.table_ddl import AddColumn, Column, Index, TableDefinition

__all__ = ["FORGE_SESSIONS", "MIGRATIONS"]

FORGE_SESSIONS = TableDefinition(
    name="forge_sessions",
    columns=[
        Column("session_id", "char", length=64),
        Column("data", "text"),
        # Identité authentifiée, recopiée de la session à chaque écriture pour
        # que la révocation soit une requête indexée et non un balayage
        # (SESSIONS-DELETE-FOR-USER-001). Nullable : une session anonyme n'a
        # pas d'utilisateur, et les lignes existantes doivent rester valides.
        # `string` et non `identity_ref` : l'identité applicative peut être un
        # entier comme une chaîne, et l'index doit rester portable.
        Column("user_id", "string", length=191, nullable=True),
        # Nature de la session (SESSIONS-TTL-PER-KIND-001). Le store portait
        # UNE durée pour tout le monde, ce qui force un arbitrage perdant :
        # réglée court, elle déconnecte les authentifiés toutes les heures ;
        # réglée long, elle laisse traîner des sessions anonymes par milliers.
        # Défaut `anonymous` : une session existante non authentifiée l'est, et
        # `authenticate` pose la nature au moment de la rotation.
        Column("kind", "string", length=20, default="anonymous"),
        Column("expire_at", "datetime"),
        Column("version", "integer", default=0),
        Column("created_at", "datetime"),
        Column("updated_at", "datetime"),
    ],
    primary_key=["session_id"],
    indexes=[
        Index("idx_forge_sessions_expire_at", "expire_at"),
        Index("idx_forge_sessions_user_id", "user_id"),
        # La métrique compte par nature (SESSIONS-ACTIVE-METRIC-001).
        Index("idx_forge_sessions_kind", "kind"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
#: Le nom conserve l'horodatage d'origine, pour que les projets déjà
#: provisionnés reconnaissent la même migration.
MIGRATIONS: list[tuple[str, TableDefinition | AddColumn]] = [
    ("20260710130000_create_forge_sessions.sql", FORGE_SESSIONS),
    # Les projets provisionnés avant SESSIONS-DELETE-FOR-USER-001 ont la table
    # sans `user_id`. La migration précédente ne se rejoue pas, son empreinte
    # étant déjà enregistrée : l'ajout passe donc par sa propre migration.
    (
        "20260901090000_add_user_id_to_forge_sessions.sql",
        AddColumn(FORGE_SESSIONS, "user_id"),
    ),
    # Même raison pour `kind` : les projets déjà provisionnés ne rejouent pas
    # la création de la table (SESSIONS-TTL-PER-KIND-001).
    (
        "20260903110000_add_kind_to_forge_sessions.sql",
        AddColumn(
            FORGE_SESSIONS, "kind",
            index_names=("idx_forge_sessions_kind",),
        ),
    ),
]
