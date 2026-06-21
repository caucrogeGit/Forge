# Statistiques : référence

> **Module extrait** : le code statistiques vit dans `forge-mvc-stats`.
> Voir `packages/forge-mvc-stats/README.md` pour l'installation et l'API utilisateur.

`forge_mvc_stats` fournit un socle d'événements statistiques **explicite** : définir un événement, le stocker, le tracker volontairement, le consulter et l'agréger.
Aucun tracking automatique, aucun cookie visiteur, aucune IP.

## Référence par module

| Module | Page | Contenu |
|---|---|---|
| `events.py` | [Les événements](references/events.md) | `StatsEvent`, validation des noms |
| `schema.py` | [La table SQL](references/schema.md) | `forge_stats_events`, SQL de création |
| `tracking.py` | [Le tracking](references/tracking.md) | `track_event`, insertion explicite |
| `admin.py` | [L'affichage admin](references/admin.md) | lister et filtrer les événements |
| `aggregate.py` | [L'agrégation](references/aggregate.md) | compter par dimension (ADR-037) |

## Principe directeur

Forge ne trace rien automatiquement.
Le développeur appelle `track_event()` quand il le décide, et injecte lui-même l'exécuteur SQL (`execute`, `fetch_all`) : Forge ne crée jamais de connexion ni ne lit la base de son propre chef.
Les noms d'événements sont des chaînes `snake_case` définies par l'application (principe 1).
