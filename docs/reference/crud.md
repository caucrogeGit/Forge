# Relations avancées et CRUD enrichi


Relations déclaratives, pivot enrichi, relations ordonnées, CRUD serveur enrichi
et amélioration HTMX optionnelle. Forge reste SQL visible, pas d'ORM.

### Relations — `many_to_many`

Une relation `many_to_many` se déclare dans `mvc/entities/relations.json`. Forge
génère la table pivot SQL via `forge sync:relations` et le CRUD via `forge make:crud`
côté source uniquement.

Champs obligatoires :

| Clé | Rôle |
|---|---|
| `type` | `"many_to_many"` |
| `source` | nom de la table source (identifiant SQL) |
| `target` | nom de la table cible (identifiant SQL) |
| `pivot_table` | nom de la table pivot |
| `source_key` | colonne FK vers la source dans le pivot |
| `target_key` | colonne FK vers la cible dans le pivot |

Exemple minimal :

```json
{
  "type": "many_to_many",
  "source": "article",
  "target": "tag",
  "pivot_table": "article_tag",
  "source_key": "article_id",
  "target_key": "tag_id"
}
```

`make:crud Article` génère un `<select multiple>` côté source, les fonctions
d'ajout/synchronisation pivot et l'affichage des libellés liés dans list/show.
Le CRUD `Tag` ne reçoit pas de champ inverse automatique. Le SQL généré est
toujours lisible et explicite — Forge ne crée pas d'ORM.

### Relations — Pivot enrichi (`pivot_fields`)

Des colonnes supplémentaires peuvent être ajoutées à la table pivot via
`pivot_fields`. Forge les inclut dans le `CREATE TABLE` généré par
`sync:relations`. Chaque champ pivot déclare `name`, `sql_type` et `nullable`.

```json
{
  "type": "many_to_many",
  "source": "article",
  "target": "tag",
  "pivot_table": "article_tag",
  "source_key": "article_id",
  "target_key": "tag_id",
  "pivot_fields": [
    { "name": "position", "sql_type": "INT", "nullable": false },
    { "name": "note", "sql_type": "VARCHAR(255)", "nullable": true }
  ]
}
```

Les champs pivot ne font pas partie de la clé primaire composite. Forge ne crée
pas d'index automatique sur eux. La saisie et l'édition de ces valeurs en
formulaire CRUD ne sont pas encore générées automatiquement.

### Relations — Relations ordonnées hors média (`order_column`)

`order_column` est un champ optionnel sur une relation `many_to_many`. Quand il
est déclaré, les requêtes `list` et `show` générées par `make:crud` trient les
libellés liés par cette colonne pivot plutôt que par le libellé de la cible.

Règles :

- doit être un identifiant SQL valide ;
- doit référencer un champ existant dans `pivot_fields` ;
- ne crée aucune colonne SQL supplémentaire (le champ doit être dans `pivot_fields`).

```json
{
  "type": "many_to_many",
  "source": "article",
  "target": "tag",
  "pivot_table": "article_tag",
  "source_key": "article_id",
  "target_key": "tag_id",
  "pivot_fields": [
    { "name": "position", "sql_type": "INT", "nullable": false }
  ],
  "order_column": "position"
}
```

| Contexte | Sans `order_column` | Avec `order_column` |
|---|---|---|
| list (labels groupés) | `ORDER BY target.label_col` | `ORDER BY pivot.position` |
| show (labels d'une fiche) | `ORDER BY target.label_col` | `ORDER BY pivot.position` |
| `CREATE TABLE` | inchangé | inchangé |

Les médias disposent de leur propre mécanisme de position et ne sont pas
concernés par cette convention.

### CRUD — Recherche, filtres, tri et pagination

Le CRUD enrichi reste **serveur d'abord** :

```
requête HTTP → contrôleur généré → SQL explicite → rendu Jinja → HTML classique
```

- **Recherche** : paramètre `q`, `LIKE %q%` sur les colonnes texte déclarées
  avec `"list": {"searchable": true}` → voir `### Listes CRUD générées : recherche et pagination`
- **Filtres simples** : déclarés avec `"list": {"filter": true}` sur un champ ;
  filtres relationnels automatiques pour les `many_to_one` → voir
  `### Listes CRUD générées : filtres simples` et
  `### Listes CRUD générées : filtres relationnels many_to_one`
- **Tri** : paramètre `sort` + `direction`, sécurisé par allowlist des colonnes
  déclarées dans l'entité → voir `### Listes CRUD générées : tri simple`
- **Pagination** : paramètre `page`, bornes, SQL `LIMIT`/`OFFSET` explicites ;
  `q`, `filters`, `sort`, `direction` conservés dans les liens de pagination
  → voir `### Listes CRUD générées : recherche et pagination`

### CRUD — États vides contextuels

Les listes générées distinguent quatre états selon les paramètres actifs :

| Condition | Message affiché |
|---|---|
| Aucun résultat avec `q` | « Aucun résultat pour votre recherche » |
| Aucun résultat avec filtres | « Aucun résultat pour les filtres sélectionnés » |
| Aucun résultat avec `q` + filtres | « Aucun résultat pour cette combinaison » |
| Table vide sans paramètre | « Aucun élément » |

→ voir `### Listes CRUD générées : états vides contextuels`

### CRUD — HTMX optionnel

HTMX est une amélioration **optionnelle et progressive**. Le CRUD HTML classique
reste fonctionnel sans JavaScript.

- Le générateur produit trois partials réutilisables : `_table.html`,
  `_pagination.html`, `_results.html`
- La **recherche HTMX** remplace la zone de résultats sans rechargement complet
- La **pagination HTMX** recharge uniquement la zone de résultats via `_results.html`
- La **suppression HTMX** retire la ligne du DOM après confirmation, avec
  fallback HTML classique (URLs et formulaires POST conservés)
- Pas de SPA, pas de dépendance à un framework JS lourd

→ voir `### Partials CRUD générés`

### Limites actuelles

- Pas d'ORM — le SQL reste explicite et visible dans le code généré ;
- pas de saisie/édition des valeurs `pivot_fields` dans les formulaires CRUD
  (colonne présente en base, non liée aux formulaires générés) ;
- pas de drag-and-drop pour les relations ordonnées ;
- pas d'endpoint de réordonnancement généré automatiquement ;
- pas de dashboard ou de navigation relationnelle entre entités ;
- pas de gestion inverse automatique côté cible pour les `many_to_many` ;
- pas de génération API JSON ;
- pas de CRUD SPA ;
- pas de modification implicite des relations existantes par le générateur.

