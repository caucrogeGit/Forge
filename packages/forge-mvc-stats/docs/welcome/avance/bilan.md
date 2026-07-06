# Bilan : niveau avancé (Stats)

Récapitulatif du **niveau avancé** de la progression *Welcome Stats*.
Ce niveau couvre la **consultation** des événements.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 : [Le SQL de consultation](stats-admin-sql.md) | Voir le `SELECT` filtrable (`get_stats_events_admin_sql`). |
| 2 : [Lister les événements](stats-list.md) | Lire via `fetch_all` injecté, normalisé (`list_stats_events`). |
| 3 : [Normaliser une ligne](stats-normalize.md) | Transformer une ligne brute en dict propre (`normalize_stats_event_row`). |

Vous maîtrisez Forge Stats de bout en bout : événement, enregistrement, consultation.

## Et ensuite

La progression *Welcome Stats* est terminée.
En production : appliquez le schéma (`get_stats_events_schema_sql`), passez `core.database.db.execute` / `fetch_all` aux fonctions de tracking et de consultation.
SQL visible partout, code testable par injection.

[Aide-mémoire de la progression Stats](../recapitulatif.md)
