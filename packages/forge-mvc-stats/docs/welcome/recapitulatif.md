# Aide-mémoire de la progression Stats

Récapitulatif des paliers de la progression *Welcome Stats* et des API du module opt-in `forge-mvc-stats` introduites à chaque étape.

!!! note "Module opt-in : SQL visible"
    `forge-mvc-stats` est **publié sur PyPI** : `pip install --pre forge-mvc-stats`.
    Il expose le **SQL réel** (schéma, insert, select), aucun ORM (charte principe 5), et s'appuie sur des **exécuteurs injectables** (`execute`, `fetch_all`), donc testable sans base réelle.

## Niveau débutant : l'événement & le schéma

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Welcome Stats](debutant/stats-welcome.md) | Créer un événement, inspecter table/colonnes | `make_event`, `STATS_EVENTS_TABLE` |
| 2 | [Nom d'événement](debutant/stats-event.md) | Normaliser/valider un nom | `normalize_event_name`, `validate_event_name` |
| 3 | [Le schéma SQL](debutant/stats-schema.md) | Lire le `CREATE TABLE` | `get_stats_events_schema_sql` |

## Niveau intermédiaire : enregistrer

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Le SQL d'insertion](intermediaire/stats-track-sql.md) | Voir l'`INSERT` et ses valeurs | `get_track_event_sql`, `prepare_track_event_values` |
| 2 | [Enregistrer un événement](intermediaire/stats-track.md) | Tracker via un exécuteur injecté | `track_event` |
| 3 | [Valider un événement](intermediaire/stats-validate.md) | Refuser avant d'écrire | `make_event`, `validate_event` |

## Niveau avancé : consulter

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Le SQL de consultation](avance/stats-admin-sql.md) | Voir le `SELECT` filtrable | `get_stats_events_admin_sql` |
| 2 | [Lister les événements](avance/stats-list.md) | Lire via `fetch_all` injecté | `list_stats_events` |
| 3 | [Normaliser une ligne](avance/stats-normalize.md) | Ligne brute → dict propre | `normalize_stats_event_row` |
