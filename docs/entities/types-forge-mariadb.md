# Mapping des types Forge vers MariaDB

Dans les JSON canoniques Forge, les champs utilisent des **types Forge**, pas des types SQL.

```json
{ "name": "title", "type": "string", "max_length": 255 }
```

`VARCHAR(255)` est une **projection SQL** dérivée par Forge lors de la génération — elle n'apparaît pas dans le JSON canonique. `sql_type` et `python_type` ne sont pas des clés canoniques.

---

## Table de mapping

| Type Forge | SQL MariaDB | Python | Notes |
|---|---|---|---|
| `string` | `VARCHAR(n)` | `str` | n = `max_length` (défaut 255) |
| `text` | `TEXT` | `str` | |
| `integer` | `INT` | `int` | |
| `big_integer` | `BIGINT` | `int` | |
| `float` | `DOUBLE` | `float` | |
| `decimal` | `DECIMAL(p,s)` | `float` | `precision` et `scale` obligatoires |
| `boolean` | `BOOLEAN` | `bool` | |
| `date` | `DATE` | `date` | |
| `datetime` | `DATETIME` | `datetime` | |
| `email` | `VARCHAR(255)` | `str` | longueur fixe, non configurable |
| `password` | `VARCHAR(255)` | `str` | longueur fixe, non configurable |
| `json` | `LONGTEXT` | `str` | contenu JSON sérialisé |

---

## Champs système automatiques

Ces champs sont **injectés automatiquement** par Forge — ils ne sont pas déclarés dans `fields[]`.

| Source | SQL MariaDB | Condition |
|---|---|---|
| `id` (toujours) | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | toutes les entités |
| `created_at` | `DATETIME NOT NULL` | `options.timestamps: true` |
| `updated_at` | `DATETIME NULL` | `options.timestamps: true` |
| `deleted_at` | `DATETIME NULL` | `options.soft_delete: true` |

---

## Types avec paramètres

### string

```json
{
  "name": "title",
  "type": "string",
  "max_length": 255
}
```

Projection :

```sql
title VARCHAR(255)
```

Si `max_length` est absent, Forge utilise 255 par défaut (comportement conservateur documenté dans le code). La valeur doit être un entier positif.

### decimal

```json
{
  "name": "price",
  "type": "decimal",
  "precision": 10,
  "scale": 2
}
```

Projection :

```sql
price DECIMAL(10,2)
```

`precision` (chiffres significatifs) et `scale` (chiffres après la virgule) sont **obligatoires** pour le type `decimal`. Forge lève une erreur immédiate si l'un des deux est absent.

---

## Contraintes courantes

### Nullabilité

| JSON canonique | SQL généré |
|---|---|
| rien (absent) | `NULL` (défaut) |
| `"nullable": true` | `NULL` |
| `"nullable": false` | `NOT NULL` |
| `"required": true` | `NOT NULL` |
| `"required": false` | `NULL` |
| `"required": true` + `"nullable": true` | `NOT NULL` (`required` prioritaire) |

**Règle** (ADR-013) : un champ est nullable par défaut. `required: true` rend le champ `NOT NULL`,
même si `nullable: true` est déclaré. Cette règle s'applique uniformément aux `fields[]` d'entité
et aux `pivot.fields[]`.

### unique

```json
{ "name": "slug", "type": "string", "max_length": 100, "unique": true }
```

Génère une contrainte :

```sql
UNIQUE KEY uk_<table>_<field> (<colonne>)
```

### default

```json
{ "name": "status", "type": "string", "max_length": 20, "default": "draft" }
```

Génère :

```sql
status VARCHAR(20) DEFAULT 'draft'
```

Valeurs spéciales :

| Valeur JSON | SQL généré |
|---|---|
| `null` | `DEFAULT NULL` |
| `true` / `false` | `DEFAULT 1` / `DEFAULT 0` |
| chaîne | `DEFAULT 'valeur'` (apostrophes échappées) |
| entier / flottant | `DEFAULT n` |

### min / max

Les clés `min` et `max` sont conservées dans la structure interne et peuvent être utilisées pour la validation applicative. Elles ne génèrent pas de contrainte SQL `CHECK`.

---

## Champs dans les tables pivot

`pivot.fields[]` utilise les **mêmes types Forge** que `fields[]`, avec le même mapping SQL.

```json
{
  "name": "role",
  "type": "string",
  "max_length": 50,
  "required": true
}
```

Projection dans la table pivot :

```sql
role VARCHAR(50) NOT NULL
```

Les contraintes `required`, `nullable`, `unique` et `default` fonctionnent de la même façon — à l'exception du **défaut de nullabilité** mentionné ci-dessus.

`pivot.fields[]` ne peut pas redéclarer `id`, `from_key` ni `to_key` — ces noms sont réservés et détectés par `FORGE_PIVOT_RESERVED_FIELD` dans `forge entity:validate`.

---

## Ce qu'il ne faut pas écrire dans le JSON canonique

Ces éléments appartiennent au SQL généré ou à l'ancien format legacy :

| Interdit | Remplacé par |
|---|---|
| `"sql_type": "VARCHAR(255)"` | `"type": "string", "max_length": 255` |
| `"python_type": "str"` | (dérivé automatiquement) |
| `"type": "VARCHAR(255)"` | `"type": "string", "max_length": 255` |
| `"type": "INT"` | `"type": "integer"` |
| `"type": "BIGINT"` | `"type": "big_integer"` |
| `"type": "TEXT"` | `"type": "text"` |
| `"type": "DATETIME"` | `"type": "datetime"` |
| `"primary_key": true` | (géré automatiquement par Forge) |
| `"auto_increment": true` | (géré automatiquement par Forge) |

---

## Limites

- Cette page décrit le mapping réellement généré par Forge — elle reflète le comportement du code, pas des spécifications théoriques.
- La nullabilité par défaut diffère entre `fields[]` et `pivot.fields[]` : déclarer explicitement `nullable` ou `required` est recommandé pour les deux cas.
- `min` et `max` sont préservés dans la structure interne mais ne produisent pas de contrainte SQL `CHECK`.
- `forge entity:validate` reste la validation officielle avant toute génération.
- VS Code aide à la saisie via `$schema`, mais ne remplace pas `entity:validate`.
