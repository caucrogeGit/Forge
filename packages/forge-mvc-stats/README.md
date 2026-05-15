# forge-mvc-stats

Module stats pour Forge — événements génériques, schéma SQL, tracking et consultation.

Extrait du core Forge depuis la version 2.8.0 (ADR-004).

## Installation

```bash
pip install forge-mvc-stats
# ou en mode developpement
pip install -e packages/forge-mvc-stats/
```

## Usage

```python
from forge_mvc_stats import make_event, track_event

# Créer un événement
event = make_event(
    "page_view",
    label="Vue de page",
    category="traffic",
    metadata={"path": "/contact"},
)

# Enregistrer dans la base (db.execute est fourni par l'application)
track_event(db.execute, event)

# Raccourci direct par nom
track_event(db.execute, "contact_click", label="Clic contact")
```

## Consultation

```python
from forge_mvc_stats import list_stats_events

# Lister les 50 derniers événements (fetch_all est fourni par l'application)
events = list_stats_events(my_fetch_all)

# Filtrer par nom ou catégorie
page_views = list_stats_events(my_fetch_all, name="page_view")
traffic    = list_stats_events(my_fetch_all, category="traffic", limit=100)
```

## Schéma SQL

```python
from forge_mvc_stats import get_stats_events_schema_sql, STATS_EVENTS_TABLE

print(STATS_EVENTS_TABLE)           # "forge_stats_events"
sql = get_stats_events_schema_sql() # CREATE TABLE IF NOT EXISTS forge_stats_events (...)
```

## Cas d'usage

- Comptage de visites de pages
- Suivi de clics sur des liens ou boutons
- Mesure de soumissions de formulaires
- Traçage d'événements métier applicatifs

## API publique

- `StatsEvent` — dataclass d'événement (name, label, category, metadata)
- `StatsEventError` — exception de validation
- `make_event(name, label, category, metadata)` — crée et valide un événement
- `validate_event(event)` — valide un événement existant
- `normalize_event_name(value)` — normalise en snake_case
- `validate_event_name(value)` — valide un nom normalisé
- `STATS_EVENTS_TABLE` — nom de la table SQL (`forge_stats_events`)
- `STATS_EVENTS_COLUMNS` — tuple des colonnes
- `get_stats_events_schema_sql()` — SQL `CREATE TABLE IF NOT EXISTS`
- `track_event(execute, event_or_name, ...)` — enregistre un événement en base
- `get_track_event_sql()` — SQL `INSERT` paramétré
- `prepare_track_event_values(event)` — tuple de paramètres prêts pour `execute`
- `list_stats_events(fetch_all, name, category, limit)` — liste des événements normalisés
- `get_stats_events_admin_sql(name, category, limit)` — SQL `SELECT` filtré
- `prepare_stats_events_admin_params(name, category, limit)` — paramètres du SELECT
- `normalize_stats_event_row(row)` — normalise une ligne brute (metadata JSON → dict)
- `StatsAdminError` — exception de consultation
