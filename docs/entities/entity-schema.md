# Schéma des entités : entity.schema.json

`schemas/entity.schema.json` verrouille la **structure autorisée** des fichiers d'entités canoniques Forge — c'est-à-dire les fichiers `mvc/entities/<entité>/<entité>.json`.

Ce schéma valide la **forme** d'un fichier d'entité. Il ne valide pas toute la logique métier : les règles sémantiques (unicité des noms, types cohérents, index sur champs existants…) sont vérifiées par `forge entity:validate`.

```
entity.schema.json   →  validation de structure (JSON Schema)
forge entity:validate →  validation sémantique complète
```

---

## Exemple complet minimal

```json
{
  "$schema": "../../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Article",
  "table": "article",
  "fields": [
    {
      "name": "title",
      "type": "string",
      "max_length": 255,
      "required": true
    },
    {
      "name": "content",
      "type": "text",
      "nullable": true
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

Le champ `id` (clé primaire `AUTO_INCREMENT`) n'est **pas déclaré**. Forge l'ajoute automatiquement dans toutes les projections SQL et Python.

---

## Propriétés racine

| Propriété | Obligatoire | Type | Rôle |
|---|---|---|---|
| `$schema` | recommandé | string | active l'autocomplétion et la détection d'erreurs dans VS Code |
| `schema_version` | **oui** | `"1.0"` | identifie le format canonique Forge |
| `name` | **oui** | PascalCase | nom de l'entité (`Article`, `UserProfile`) |
| `table` | **oui** | snake_case | nom de la table MariaDB (`article`, `user_profile`) |
| `label` | non | string | libellé singulier affiché dans l'interface générée |
| `plural_label` | non | string | libellé pluriel affiché dans l'interface générée |
| `description` | non | string | description fonctionnelle de l'entité |
| `fields` | **oui** | array | champs métier (au moins un) |
| `options` | non | object | options de génération (`timestamps`, `soft_delete`) |
| `indexes` | non | array | index déclaratifs supplémentaires |

Les clés inconnues sont **interdites** (`additionalProperties: false`).

**Formats attendus :**

- `name` — `^[A-Z][A-Za-z0-9]*$` — commence par une majuscule
- `table` — `^[a-z][a-z0-9_]*$` — snake_case strict

---

## fields[]

`fields[]` contient les champs métier de l'entité. Chaque champ est validé par `field.schema.json`. Au moins un champ est requis.

**Clés obligatoires de chaque champ :**

| Clé | Type | Rôle |
|---|---|---|
| `name` | snake_case | nom du champ (`title`, `published_at`) |
| `type` | enum | type Forge du champ |

**Types Forge supportés :**

`string`, `text`, `integer`, `big_integer`, `float`, `decimal`, `boolean`, `date`, `datetime`, `email`, `password`, `json`

**Clés optionnelles :**

| Clé | Rôle |
|---|---|
| `required` | champ obligatoire en formulaire (défaut : `false`) |
| `nullable` | colonne SQL accepte NULL (défaut : `true`) |
| `unique` | contrainte UNIQUE sur la colonne (défaut : `false`) |
| `max_length` | longueur max — types `string`, `email`, `password` |
| `precision` | chiffres significatifs — type `decimal` (obligatoire si `decimal`) |
| `scale` | chiffres après la virgule — type `decimal` (obligatoire si `decimal`) |
| `min` / `max` | valeur min / max — types numériques |
| `default` | valeur par défaut |
| `auto_now` | mis à jour à chaque modification — types `date`, `datetime` |
| `auto_now_add` | initialisé à la création — types `date`, `datetime` |
| `choices` | valeurs autorisées — génère un `select` dans les formulaires |
| `label` | libellé affiché dans les formulaires et listes |
| `description` | description longue du champ |
| `form` | options de rendu dans les formulaires générés |
| `crud` | visibilité dans les vues CRUD générées |

**Exemple — champ email unique :**

```json
{
  "name": "email",
  "type": "email",
  "required": true,
  "unique": true
}
```

**Exemple — champ décimal :**

```json
{
  "name": "price",
  "type": "decimal",
  "precision": 10,
  "scale": 2,
  "nullable": false
}
```

**Rappels :**

- `id` est **interdit** dans `fields[]` — c'est une clé réservée par Forge.
- Les noms de champs sont en `snake_case` : `^[a-z][a-z0-9_]*$`.
- `sql_type` et `python_type` **ne font pas partie** du format canonique — ils sont dérivés par Forge lors de la génération.

---

## options

`options` contrôle les colonnes système que Forge ajoute automatiquement à la table.

| Option | Type | Défaut | Effet |
|---|---|---|---|
| `timestamps` | boolean | `false` | génère `created_at` et `updated_at` |
| `soft_delete` | boolean | `false` | génère `deleted_at` pour la suppression logique |

Les clés inconnues dans `options` sont **interdites**.

```json
"options": {
  "timestamps": true,
  "soft_delete": false
}
```

Quand `timestamps: true`, Forge ajoute `created_at DATETIME` et `updated_at DATETIME` dans la projection SQL. Ces colonnes ne sont pas déclarées dans `fields[]`.

Quand `soft_delete: true`, Forge ajoute `deleted_at DATETIME NULL`. Les enregistrements supprimés sont conservés en base avec une date de suppression.

---

## indexes

`indexes` permet de déclarer des index MariaDB supplémentaires sur des champs existants de l'entité.

Chaque entrée d'index accepte :

| Clé | Obligatoire | Rôle |
|---|---|---|
| `name` | **oui** | nom de l'index SQL (`idx_article_title`) |
| `fields` | **oui** | liste de champs couverts (au moins un) |
| `unique` | non | index unique ? (défaut : `false`) |

```json
"indexes": [
  {
    "name": "idx_article_title",
    "fields": ["title"]
  },
  {
    "name": "uq_article_slug",
    "fields": ["slug"],
    "unique": true
  }
]
```

La **cohérence** — vérifier que les champs de l'index existent bien dans `fields[]` — est vérifiée par `forge entity:validate`, pas par le JSON Schema seul.

---

## Ce qui n'est plus canonique

Ces clés appartenaient à l'ancien format (`format_version: 1`) ou sont des projections dérivées. Elles **ne doivent pas apparaître** dans les fichiers canoniques `schema_version: "1.0"`.

| Clé interdite | Explication |
|---|---|
| `format_version` | identifiant du format legacy — remplacé par `schema_version` |
| `entity` | ancien nom de la clé `name` |
| `column` | les noms de colonnes sont dérivés automatiquement |
| `sql_type` | type SQL — projection dérivée, pas une clé canonique |
| `python_type` | type Python — projection dérivée |
| `primary_key` | la clé primaire `id` est gérée automatiquement par Forge |
| `auto_increment` | idem |
| `constraints` | ancien format des contraintes |

Le JSON Schema bloque toute clé inconnue via `additionalProperties: false`. Un fichier contenant `sql_type` sera rejeté dès la validation JSON Schema.

---

## Erreurs fréquentes

**Déclarer `id` dans `fields[]` :**

```json
{ "name": "id", "type": "integer" }
```

`id` est réservé. `forge entity:validate` rejette ce champ avec une erreur explicite.

---

**Utiliser un type SQL plutôt qu'un type Forge :**

```json
{ "name": "title", "type": "VARCHAR(255)" }
```

`VARCHAR(255)` n'est pas un type Forge. Le type canonique est `"type": "string", "max_length": 255`.

---

**Oublier `schema_version` :**

```json
{ "name": "Article", "table": "article", "fields": [...] }
```

`schema_version` est obligatoire. Sans elle, le fichier est invalide selon le JSON Schema.

---

**Utiliser `sql_type` ou `python_type` :**

Ces clés sont des projections de l'ancien format. Elles sont inconnues du schéma canonique et bloquées par `additionalProperties: false`.

---

**Déclarer un index sur un champ inexistant :**

```json
"indexes": [{ "name": "idx_x", "fields": ["nonexistent"] }]
```

Le JSON Schema ne détecte pas cette incohérence — mais `forge entity:validate` la signale avec une erreur sémantique.

---

**Utiliser une clé inconnue à la racine :**

```json
{ ..., "engine": "InnoDB" }
```

`additionalProperties: false` bloque toute clé non déclarée dans le schéma.

---

## Valider une entité

```bash
forge entity:validate
```

Sortie humaine : liste les erreurs et avertissements pour chaque fichier d'entité et le fichier de relations.

```bash
forge entity:validate --json
```

Sortie machine : JSON structuré avec `valid`, `errors_count`, `errors[]`.

```bash
forge build:model
```

Refuse de générer si `entity:validate` détecte des erreurs. `make:crud` et certaines migrations utilisent également ce garde-fou.

La commande `entity:validate` est la **validation officielle** — VS Code aide à écrire, mais ne remplace pas cette étape.
