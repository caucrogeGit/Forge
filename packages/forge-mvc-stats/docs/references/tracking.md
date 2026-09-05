# Le tracking dans Forge Stats

Ce document décrit le helper `track_event`, qui enregistre un événement dans la base.

Le fichier de code correspondant est `forge_mvc_stats/tracking.py`.

## 1. À quoi sert ce module ?

Tracker, c'est écrire un événement dans `forge_stats_events`.
Le développeur appelle `track_event()` **volontairement** : Forge ne trace rien automatiquement.

Principes :

- aucune page n'est tracée automatiquement ;
- aucun cookie visiteur n'est créé ;
- ni IP, ni user-agent, ni géolocalisation ne sont stockés ;
- l'exécuteur SQL est **injecté** par l'appelant ; `track_event()` ne crée pas de connexion.

## 2. Enregistrer un événement

```python
from forge_mvc_stats import KIND_PAGE_VIEW, track_event

track_event(
    execute=db.execute,
    event_or_name="contact",
    label="Page contact",
    category="traffic",
    metadata={"path": "/contact"},
    kind=KIND_PAGE_VIEW,
)
```

Sans `kind`, l'événement est une **action**, le défaut du contrat.
Cette page employait `"page_view"` comme nom d'événement, convention d'avant le champ : les vues de page écrites ainsi étaient comptées parmi les actions.

Avec un événement déjà construit :

```python
from forge_mvc_stats import make_event, track_event

event = make_event("contact_click", label="Clic contact", metadata={"source": "footer"})
track_event(db.execute, event)
```

Un `StatsEvent` porte déjà sa forme : lui joindre `label`, `category`, `metadata` ou `kind` est refusé.
Ces arguments étaient auparavant ignorés en silence, si bien qu'un appelant croyait poser une vue de page et écrivait une action.

## 3. L'API

| Fonction | Comportement |
|---|---|
| `get_track_event_sql()` | le SQL `INSERT INTO forge_stats_events (name, label, category, metadata) VALUES (?, ?, ?, ?)` |
| `prepare_track_event_values(event)` | le tuple `(name, label, category, metadata_json)` prêt pour l'exécution |
| `track_event(execute, event_or_name, ...)` | valide, prépare, appelle `execute(sql, params)`, retourne le `StatsEvent` |

`metadata` est sérialisée en JSON avec `sort_keys=True` ; une métadonnée non sérialisable lève `StatsEventError`.

## 4. Contextes d'utilisation

- **Contrôleur** : `track_event(db.execute, "form_submit", ...)` après une action réussie.
- **Tests** : passer un `execute` factice pour vérifier le SQL et les paramètres.

## 5. Voir aussi

- [Les événements](events.md) : l'objet enregistré.
- [La table SQL](schema.md) : la destination de l'insertion.
- [L'agrégation](aggregate.md) : compter les événements enregistrés.
