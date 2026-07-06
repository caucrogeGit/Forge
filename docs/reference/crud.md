# Relations avancées et CRUD enrichi


Relations déclaratives, pivot enrichi, relations ordonnées, CRUD serveur enrichi et amélioration HTMX optionnelle.
Forge reste SQL visible, pas d'ORM.

### Relations : `many_to_many`

Une relation `many_to_many` se déclare dans `mvc/entities/relations.json`.
Forge génère la table pivot SQL via `forge sync:relations` et le CRUD via `forge make:crud` côté source uniquement.

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

`make:crud Article` génère un `<select multiple>` côté source, les fonctions d'ajout/synchronisation pivot et l'affichage des libellés liés dans list/show.
Le CRUD `Tag` ne reçoit pas de champ inverse automatique.
Le SQL généré est toujours lisible et explicite, Forge ne crée pas d'ORM.

### Relations : Pivot enrichi (`pivot_fields`)

Des colonnes supplémentaires peuvent être ajoutées à la table pivot via `pivot_fields`.
Forge les inclut dans le `CREATE TABLE` généré par `sync:relations`.
Chaque champ pivot déclare `name`, `sql_type` et `nullable`.

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

Les champs pivot ne font pas partie de la clé primaire composite.
Forge ne crée pas d'index automatique sur eux.
La saisie et l'édition de ces valeurs en formulaire CRUD ne sont pas encore générées automatiquement.

### Relations : Relations ordonnées hors média (`order_column`)

`order_column` est un champ optionnel sur une relation `many_to_many`.
Quand il est déclaré, les requêtes `list` et `show` générées par `make:crud` trient les libellés liés par cette colonne pivot plutôt que par le libellé de la cible.

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

Les médias disposent de leur propre mécanisme de position et ne sont pas concernés par cette convention.

### CRUD : Recherche, filtres, tri et pagination

Le CRUD enrichi reste **serveur d'abord** :

```
requête HTTP → contrôleur généré → SQL explicite → rendu Jinja → HTML classique
```

- **Recherche** : paramètre `q`, `LIKE %q%` sur les colonnes texte déclarées avec `"list": {"searchable": true}` → voir `### Listes CRUD générées : recherche et pagination`
- **Filtres simples** : déclarés avec `"list": {"filter": true}` sur un champ ; filtres relationnels automatiques pour les `many_to_one` → voir `### Listes CRUD générées : filtres simples` et `### Listes CRUD générées : filtres relationnels many_to_one`
- **Tri** : paramètre `sort` + `direction`, sécurisé par allowlist des colonnes déclarées dans l'entité → voir `### Listes CRUD générées : tri simple`
- **Pagination** : paramètre `page`, bornes, SQL `LIMIT`/`OFFSET` explicites ; `q`, `filters`, `sort`, `direction` conservés dans les liens de pagination → voir `### Listes CRUD générées : recherche et pagination`

### CRUD : États vides contextuels

Les listes générées distinguent quatre états selon les paramètres actifs :

| Condition | Message affiché |
|---|---|
| Aucun résultat avec `q` | « Aucun résultat pour votre recherche » |
| Aucun résultat avec filtres | « Aucun résultat pour les filtres sélectionnés » |
| Aucun résultat avec `q` + filtres | « Aucun résultat pour cette combinaison » |
| Table vide sans paramètre | « Aucun élément » |

→ voir `### Listes CRUD générées : états vides contextuels`

### CRUD : HTMX optionnel

HTMX est une amélioration **optionnelle et progressive**.
Le CRUD HTML classique reste fonctionnel sans JavaScript.

- Le générateur produit trois partials réutilisables : `_table.html`, `_pagination.html`, `_results.html`
- La **recherche HTMX** remplace la zone de résultats sans rechargement complet
- La **pagination HTMX** recharge uniquement la zone de résultats via `_results.html`
- La **suppression HTMX** retire la ligne du DOM après confirmation, avec fallback HTML classique (URLs et formulaires POST conservés)
- Pas de SPA, pas de dépendance à un framework JS lourd

→ voir `### Partials CRUD générés`

### Listes CRUD générées : filtres simples

En plus de la recherche texte `q`, chaque champ non-PK peut exposer un filtre d'égalité via la métadonnée `"list"`.

```json
{
  "name": "statut",
  "sql_type": "VARCHAR(50)",
  "python_type": "str",
  "nullable": false,
  "constraints": {},
  "list": { "filter": true }
}
```

**Types SQL supportés pour `list.filter=true`** :

| Famille | Exemples |
|---|---|
| Chaînes courtes | `VARCHAR(n)`, `CHAR(n)` |
| Entiers | `INT`, `BIGINT`, `SMALLINT`, `TINYINT`, `MEDIUMINT` |
| Booléens | `BOOL`, `BOOLEAN` |

Types **non supportés** (erreur à la validation) : `TEXT`, `DATE`, `DATETIME`, `TIMESTAMP`, `DECIMAL`, `FLOAT`, `DOUBLE`.

**Comportement généré**

- Champ `VARCHAR`/`CHAR`/`INT` → `<input type="text">` dans le formulaire de recherche.
- Champ `BOOL`/`BOOLEAN` → `<select>` avec Tous / Oui / Non.
- Valeur filtrée transmise en GET : `/contact?statut=actif&actif=1&q=roger&page=2`
- Filtres conservés dans les liens de tri et de pagination via une boucle Jinja2 générique.
- `list.filter=false` ou `"list"` absent → comportement actuel inchangé.

**SQL généré**

Recherche `q` et filtres sont combinés avec `AND` ; chaque groupe de LIKE est entre parenthèses :

```sql
SELECT * FROM contact
WHERE (Nom LIKE ? OR Email LIKE ?)
  AND Statut = ?
ORDER BY Id DESC
LIMIT ? OFFSET ?
```

Toutes les valeurs sont paramétrées (aucune concaténation directe).

**Sécurité, whitelist de colonnes filtrées**

Les noms de colonnes ne peuvent pas être passés comme paramètres SQL `?`.
Pour éviter toute injection de colonne, le modèle généré crée une allowlist explicite :

```python
_ALLOWED_FILTERS = {"statut": "Statut", "ville_id": "contact.VilleId"}

for key, val in (filters or {}).items():
    if val is not None and val != "":
        col = _ALLOWED_FILTERS.get(key)
        if col is None:
            raise ValueError(f"Filtre interdit : {key}")
        clauses.append(col + " = ?")
        params.append(val)
```

Une clé absente de `_ALLOWED_FILTERS` lève `ValueError` immédiatement.
Le contrôleur généré ne passe que des clés correspondant aux champs déclarés dans le JSON d'entité ; une clé injectée manuellement depuis une URL GET ne peut jamais atteindre la concaténation SQL.

**Compatibilité HTMX et réinitialisation**

Le formulaire de filtres est un formulaire `GET` standard avec une amélioration HTMX progressive.
Sans HTMX, le formulaire recharge la page complète.
Avec HTMX, le formulaire remplace uniquement la zone `#crud-results` et pousse l'URL dans l'historique.

Un lien « Réinitialiser »
est généré dans le formulaire.
Il s'affiche dès que `pagination.q` est non vide **ou** que `pagination.filters` contient au moins un filtre actif.
Le lien a un `href` classique (fallback sans JavaScript) et les attributs HTMX pour une navigation fluide.

```html
{% if pagination.q or pagination.filters %}
<a href="/contact"
   hx-get="/contact" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true">
  Réinitialiser
</a>
{% endif %}
```

Aucun JavaScript personnalisé, aucune recherche live et aucun `debounce` ne sont générés.

**Limites des filtres CRUD**

Les filtres générés par `list.filter=true` sont des filtres d'égalité simples.
Ne sont pas supportés dans cette version :

- opérateurs avancés : `>`, `<`, `BETWEEN`, `IN`, `NOT IN` ;
- filtres multi-valeurs (checkboxes multiples) ;
- plages de dates ou de nombres ;
- filtres relationnels profonds (jointures imbriquées) ;
- recherche live automatique à la saisie ;
- debounce ou auto-submit sur changement de valeur ;
- filtres sauvegardés en session ou en base ;
- API JSON CRUD avec filtres.

Ces extensions peuvent être ajoutées manuellement dans les fichiers générés.

### Listes CRUD générées : filtres relationnels `many_to_one`

Une relation `many_to_one` déclarée dans `mvc/entities/relations.json` peut aussi être utilisée comme filtre de liste.
Aucune nouvelle métadonnée obligatoire n'est nécessaire : la présence de la relation suffit.

Exemple minimal :

```json
{
  "name": "hebergement_commune",
  "type": "many_to_one",
  "from_entity": "Hebergement",
  "to_entity": "Commune",
  "from_field": "commune_id",
  "to_field": "id",
  "foreign_key_name": "fk_hebergement_commune",
  "on_delete": "RESTRICT",
  "on_update": "CASCADE"
}
```

URL :

```text
/hebergements?commune_id=3
/hebergements?q=gite&commune_id=3&page=2
```

Le filtre relationnel est rendu sous forme de `<select>` :

```html
<select name="commune_id">
  <option value="">Tous les Commune</option>
  ...
</select>
```

Forge charge les options depuis l'entité liée avec une fonction modèle explicite.
Le libellé est déduit du premier champ textuel disponible (`VARCHAR`, `CHAR`, `TEXT`) ; si l'entité liée n'a aucun champ textuel, Forge utilise la clé primaire comme libellé.
Les options sont triées par ce libellé, ou par la clé primaire en fallback.

Le contrôleur généré ignore une valeur vide ou non numérique.
La valeur valide est passée comme paramètre SQL, puis combinée avec `q`, les filtres simples, la pagination et le tri.

Le formulaire create/edit continue d'utiliser `RelationField`.
Les fonctionnalités plus avancées comme l'autocomplete ou la recherche dans les options ne font pas partie de cette première version.

**Contexte de vue**

`pagination.filters` est toujours un dict (vide si aucun filtre actif) :

```python
pagination = {
    "page": 1, "nb_pages": 3, "total": 55,
    "has_prev": False, "has_next": True,
    "q": "roger", "sort": "", "direction": "desc",
    "filters": {"statut": "actif", "actif": "1"},
}
```

### Limites actuelles

- Pas d'ORM, le SQL reste explicite et visible dans le code généré ;
- pas de saisie/édition des valeurs `pivot_fields` dans les formulaires CRUD (colonne présente en base, non liée aux formulaires générés) ;
- pas de drag-and-drop pour les relations ordonnées ;
- pas d'endpoint de réordonnancement généré automatiquement ;
- pas de dashboard ou de navigation relationnelle entre entités ;
- pas de gestion inverse automatique côté cible pour les `many_to_many` ;
- pas de génération API JSON ;
- pas de CRUD SPA ;
- pas de modification implicite des relations existantes par le générateur.

