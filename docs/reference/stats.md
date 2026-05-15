# Statistiques — Événements simples

> **Module extrait** : depuis Forge 2.8.0, le code statistiques vit dans
> `forge-mvc-stats`. Voir `packages/forge-mvc-stats/README.md` pour
> l'installation et l'API utilisateur. Cette page documente l'API publique
> pour mémoire et référence rapide.


`forge_mvc_stats` fournit une structure d'événement statistique générique. Ce ticket pose uniquement le **contrat des événements** : définition, normalisation et validation. Aucun stockage, aucun tracking automatique.

**Ce que ce module fait :**

- Définir un événement statistique (`StatsEvent`) avec un nom, un libellé, une catégorie et des métadonnées.
- Normaliser et valider les noms d'événements en snake_case.
- Fournir des constantes pour les événements courants recommandés.

**Ce que ce module ne fait pas encore :**

- Aucun stockage SQL (prévu dans STATS-002).
- Aucun helper de tracking (`track_event(...)`) (prévu dans STATS-003).
- Aucun affichage admin (prévu dans STATS-004).
- Aucun middleware, aucune session visiteur, aucun cookie, aucune IP.

### `StatsEvent`

```python
@dataclass(frozen=True)
class StatsEvent:
    name: str                    # snake_case, obligatoire
    label: str = ""              # fallback vers name si vide
    category: str = "general"   # fallback vers "general" si vide
    metadata: dict[str, Any] = field(default_factory=dict)
```

Immuable (`frozen=True`). Le constructeur valide et normalise `name`. `metadata` doit être un dictionnaire — `None` est remplacé par `{}`.

### API

```python
from forge_mvc_stats import (
    StatsEvent, StatsEventError,
    normalize_event_name, validate_event_name,
    make_event, validate_event,
)

e = make_event(
    "page_view",
    label="Vue de page",
    category="traffic",
    metadata={"path": "/contact"},
)
# StatsEvent(name='page_view', label='Vue de page', category='traffic', ...)

validate_event(e)          # retourne e
```

Les noms d'événements sont de simples chaînes `snake_case` définies par l'application. Forge ne fournit pas de liste de noms prédéfinis — conformément au Principe 1 de la Charte Forge (le framework n'est pas l'application).

### Fonctions

| Fonction | Comportement |
|---|---|
| `normalize_event_name(value)` | Lowercase, espaces et tirets → `_`. Lève si chars interdits. |
| `validate_event_name(value)` | Normalise puis vérifie le format `[a-z][a-z0-9_]*`. Lève sinon. |
| `make_event(name, ...)` | Crée un `StatsEvent` validé. |
| `validate_event(event)` | Vérifie que `event` est un `StatsEvent`. Retourne l'événement ou lève. |

**Noms courants** (chaînes à utiliser directement) : `"page_view"`, `"contact_click"`, `"form_submit"`, `"download_click"`, `"external_link_click"`, `"media_view"`. Ces noms sont valides mais ne sont pas des constantes exportées par Forge.

---

### Statistiques — Table SQL générique

`forge_mvc_stats` expose la définition SQL de la table `forge_stats_events`. Cette table est destinée à stocker les événements définis par STATS-001, une fois le helper de tracking ajouté dans STATS-003.

**Ce ticket ne fait pas encore :**

- Aucun enregistrement automatique d'événement.
- Aucune page tracée automatiquement.
- Aucun cookie ni session visiteur.
- Aucun helper `track_event()` (prévu dans STATS-003).
- Aucun affichage admin (prévu dans STATS-004).

#### Structure de la table

Nom : `forge_stats_events`

| Colonne | Type | Description |
|---|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT` | Identifiant technique |
| `name` | `VARCHAR(100) NOT NULL` | Nom normalisé de l'événement |
| `label` | `VARCHAR(150) NOT NULL` | Libellé humain |
| `category` | `VARCHAR(100) DEFAULT 'general'` | Catégorie générique |
| `metadata` | `JSON NULL` | Données complémentaires optionnelles |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | Date de création |

Index : `name`, `category`, `created_at`.

#### API

```python
from forge_mvc_stats import (
    STATS_EVENTS_TABLE,
    STATS_EVENTS_COLUMNS,
    get_stats_events_schema_sql,
)

print(STATS_EVENTS_TABLE)      # "forge_stats_events"
print(STATS_EVENTS_COLUMNS)    # ("id", "name", "label", "category", "metadata", "created_at")

sql = get_stats_events_schema_sql()
# → "CREATE TABLE IF NOT EXISTS forge_stats_events ( ... )"
```

`get_stats_events_schema_sql()` retourne la chaîne SQL complète de création de table, sans accès à la base de données. Elle peut être utilisée dans un script de migration ou de setup.

---

### Statistiques — Helper Python de tracking

`forge_mvc_stats` fournit un helper Python explicite pour enregistrer un événement dans la table `forge_stats_events`. **Le développeur doit appeler `track_event()` volontairement** — Forge ne trace rien automatiquement.

**Principes :**

- Aucune page n'est tracée automatiquement.
- Aucun cookie visiteur n'est créé.
- Ni IP, ni user-agent, ni géolocalisation ne sont stockés.
- L'exécuteur SQL est injecté par l'appelant — `track_event()` ne crée pas de connexion.

#### Exemple d'utilisation

```python
from forge_mvc_stats import track_event

# db.execute est l'exécuteur SQL de l'application (ex. connexion Forge)
track_event(
    execute=db.execute,
    event_or_name="page_view",
    label="Vue de page",
    category="traffic",
    metadata={"path": "/contact"},
)
```

Avec un événement déjà construit :

```python
from forge_mvc_stats import make_event, track_event

event = make_event("contact_click", label="Clic contact", metadata={"source": "footer"})
track_event(db.execute, event)
```

#### API

| Fonction | Comportement |
|---|---|
| `get_track_event_sql()` | Retourne le SQL `INSERT INTO forge_stats_events (name, label, category, metadata) VALUES (?, ?, ?, ?)`. |
| `prepare_track_event_values(event)` | Retourne un tuple `(name, label, category, metadata_json)` prêt pour l'exécution SQL. |
| `track_event(execute, event_or_name, ...)` | Valide l'événement, prépare les valeurs, appelle `execute(sql, params)`, retourne le `StatsEvent`. |

`metadata` est sérialisée en JSON avec `sort_keys=True`. Une metadata non sérialisable lève `StatsEventError`.

### Statistiques — Affichage admin simple

`forge_mvc_stats` fournit une API de consultation des événements enregistrés dans `forge_stats_events`. **Le développeur injecte la fonction `fetch_all`** — Forge ne lit jamais la base automatiquement.

- Aucun dashboard graphique, aucun middleware, aucun cookie de session.
- Filtres optionnels : `name`, `category`. Limite bornée à 500 lignes.
- Métadonnées JSON désérialisées automatiquement en `dict`.

```python
from forge_mvc_stats import list_stats_events

def my_fetch_all(sql, params):
    # votre connexion MariaDB/SQLite ici
    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]

# Lister les 50 derniers événements
events = list_stats_events(my_fetch_all)

# Filtrer par nom
page_views = list_stats_events(my_fetch_all, name="page_view", limit=100)

# Filtrer par catégorie
traffic = list_stats_events(my_fetch_all, category="traffic")
```

Chaque entrée retournée est un `dict` normalisé :

```python
{
    "id": 42,
    "name": "page_view",
    "label": "Vue de page",
    "category": "traffic",
    "metadata": {"path": "/contact"},   # toujours un dict
    "created_at": "2026-05-08 10:00:00",
}
```

#### API

| Fonction | Comportement |
|---|---|
| `get_stats_events_admin_sql(name, category, limit)` | Retourne le SQL `SELECT ... FROM forge_stats_events WHERE 1 = 1 [AND name = ?] [AND category = ?] ORDER BY created_at DESC, id DESC LIMIT ?`. |
| `prepare_stats_events_admin_params(name, category, limit)` | Valide et retourne le tuple de paramètres SQL. `name` est normalisé via `validate_event_name()`. `limit` est borné à 500. |
| `normalize_stats_event_row(row)` | Normalise une ligne brute : désérialise `metadata` JSON, `None`/`""` → `{}`. Lève `StatsAdminError` si colonnes manquantes ou JSON invalide. |
| `list_stats_events(fetch_all, name, category, limit)` | Orchestre la requête et retourne une liste de dicts normalisés. |

