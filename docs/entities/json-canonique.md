# Le JSON canonique dans Forge

Dans Forge, les fichiers JSON d'entités et de relations sont la **source canonique**. Ils décrivent le modèle métier. Les générateurs produisent ensuite des projections SQL et Python à partir de ces fichiers.

Modifier les fichiers JSON, c'est faire évoluer le modèle. Modifier les projections générées manuellement n'a pas d'effet durable — elles seront écrasées à la prochaine génération.

---

## Principe central

```
JSON canonique          →  source de vérité
JSON Schema             →  contrat de forme
entity:validate         →  diagnostic officiel
build:model             →  génération des projections
```

Le JSON ne contient pas de `sql_type`, ni de `python_type`, ni de `primary_key`. Ces éléments sont **dérivés par Forge** lors de la génération. Le champ `id` est géré automatiquement — il n'est pas à déclarer dans le JSON canonique.

---

## Structure des fichiers

Chaque entité vit dans son propre sous-dossier, nommé en **minuscule** (snake_case).
Le fichier JSON de l'entité porte le même nom que le dossier.

```text
mvc/
└── entities/
    ├── article/
    │   └── article.json      ← source canonique de l'entité Article
    ├── tag/
    │   └── tag.json          ← source canonique de l'entité Tag
    └── relations.json        ← relations globales (many_to_one, many_to_many)
```

**Règles :**

- `mvc/entities/<nom>/<nom>.json` — un sous-dossier par entité, nom en minuscule.
- `mvc/entities/relations.json` — à la racine de `entities/`, pas dans un sous-dossier.
- Un fichier JSON placé directement dans `mvc/entities/` (ex : `mvc/entities/article.json`) n'est **pas** reconnu par `build:model`.

Exemples de chemins valides :

- `mvc/entities/article/article.json`
- `mvc/entities/tag/tag.json`
- `mvc/entities/user_profile/user_profile.json`
- `mvc/entities/relations.json`

**Comportement de `build:model` :**

`build:model` parcourt les sous-dossiers de `mvc/entities/`. Pour chaque sous-dossier dont le nom ne commence pas par `__`, il s'attend à trouver un fichier JSON du même nom. Tout sous-dossier sans fichier JSON correspondant déclenche une erreur.

Les dossiers préfixés par `__` (ex : `__media/`) sont ignorés — ils servent à isoler des ressources techniques non-entités.

---

## Fichiers concernés

| Fichier | Rôle |
|---|---|
| `mvc/entities/<entite>/<entite>.json` | Source canonique de l'entité (champs métier) |
| `mvc/entities/relations.json` | Source canonique des relations entre entités |
| `schemas/entity.schema.json` | Contrat JSON Schema d'une entité Forge |
| `schemas/field.schema.json` | Contrat JSON Schema d'un champ métier |
| `schemas/relations.schema.json` | Contrat JSON Schema du fichier de relations |
| `schemas/pivot.schema.json` | Contrat JSON Schema d'une table pivot |
| `schemas/common.schema.json` | Définitions partagées (noms de tables, colonnes…) |

Les schémas JSON Schema verrouillent la **forme autorisée**. Ils ne remplacent pas la validation sémantique Forge, qui va plus loin (unicité des noms, types cohérents, collisions interdites…).

---

## Format d'une entité canonique

```json
{
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
      "name": "published_at",
      "type": "datetime",
      "nullable": true
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

**Clés principales :**

- `schema_version: "1.0"` — active le format canonique
- `name` — nom de l'entité (PascalCase)
- `table` — nom de la table SQL (snake_case)
- `fields` — champs métier (le champ `id` est toujours ajouté automatiquement)
- `options` — options système (`timestamps`, `soft_delete`)

**Types de champs supportés :** `string`, `text`, `integer`, `big_integer`, `float`, `decimal`, `boolean`, `date`, `datetime`, `email`, `password`, `json`.

---

## Flux Forge

```
JSON canonique (mvc/entities/)
    │
    ▼
forge entity:validate
    │  validation JSON Schema (structure)
    │  validation sémantique Forge (cohérence)
    │
    ▼
forge build:model
    │
    ├── <entite>.sql        projection SQL de la table
    ├── <entite>_base.py    base Python générée
    └── relations.sql       SQL des contraintes relationnelles
```

`forge entity:validate` est la **commande de diagnostic officielle**. Elle vérifie la structure et la cohérence de tous les fichiers JSON d'entités et de relations avant toute génération.

---

## Ce qui est généré

`forge build:model` génère ou régénère :

| Fichier | Nature | Règle |
|---|---|---|
| `<entite>.sql` | Projection SQL | Régénérable — ne pas modifier manuellement |
| `<entite>_base.py` | Base Python | Régénérable — ne pas modifier manuellement |
| `relations.sql` | SQL des relations | Régénérable — ne pas modifier manuellement |
| `<entite>.py` | Classe métier | Manuel — jamais écrasé par Forge |
| `__init__.py` | Export de l'entité | Manuel — jamais écrasé par Forge |

Les fichiers manuels ne sont pas écrasés. Forge applique une règle stricte de non-réécriture silencieuse.

---

## Contrat canonique et projections

Le JSON canonique **n'est pas une copie du SQL**. Il décrit le modèle métier, pas la technique.

| JSON canonique | Projection générée |
|---|---|
| `"type": "string", "max_length": 50` | `VARCHAR(50)` |
| `"type": "integer"` | `INT` |
| `"type": "decimal", "precision": 10, "scale": 2` | `DECIMAL(10,2)` |
| `"required": true` | `NOT NULL` |
| `"nullable": true` | `NULL` |

Le champ `id` (clé primaire `AUTO_INCREMENT`) est toujours injecté par Forge — il n'apparaît pas dans les `fields` du JSON canonique.

---

## Relations

Les relations entre entités sont décrites dans `mvc/entities/relations.json`.

### many_to_one

```json
{
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_one",
      "from": "Article",
      "to": "Category",
      "name": "category",
      "foreign_key": "category_id",
      "on_delete": "restrict"
    }
  ]
}
```

Génère un `ALTER TABLE` avec une contrainte `FOREIGN KEY`.

### many_to_many

```json
{
  "type": "many_to_many",
  "from": "Article",
  "to": "Tag",
  "name": "tags",
  "pivot": {
    "table": "article_tag",
    "from_key": "article_id",
    "to_key": "tag_id",
    "id": true,
    "unique_pair": true,
    "on_delete": "cascade",
    "fields": []
  }
}
```

Génère un `CREATE TABLE` pour la table pivot avec :

- un `id` technique `AUTO_INCREMENT` (toujours présent)
- une contrainte `UNIQUE` sur `(from_key, to_key)` (toujours présente)
- deux contraintes `FOREIGN KEY`

### Attributs pivot métier (`pivot.fields`)

Des champs métier peuvent être ajoutés à la table pivot :

```json
"fields": [
  { "name": "role", "type": "string", "max_length": 50, "required": true },
  { "name": "joined_at", "type": "datetime", "nullable": true }
]
```

Les noms `id`, `from_key` et `to_key` sont réservés — les redéclarer dans `pivot.fields` est interdit et détecté par `entity:validate`.

---

## Aide à la saisie dans VS Code

Les fichiers JSON d'entités et de relations peuvent déclarer un `$schema` pour activer l'autocomplétion et la détection d'erreurs de structure dans VS Code :

```json
{
  "$schema": "../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Article",
  ...
}
```

VS Code aide à écrire, mais `forge entity:validate` reste la **validation officielle**. La documentation détaillée de l'autocomplétion VS Code sera traitée dans un ticket dédié.

---

## Limites assumées

- `forge entity:validate` est la validation officielle — VS Code aide mais ne remplace pas.
- Le format `format_version: 1` est **refusé** — `build:model` et `make:crud` lèvent une erreur si un fichier d'entité ou de relations utilise l'ancien format. Voir le guide de conversion `docs/entities/migration-legacy-vers-canonique.md`.
- Le **CRUD avancé des attributs pivot** (`pivot.fields`) n'est pas encore couvert par `make:crud`.
- La documentation détaillée des schémas JSON (`entity.schema.json`, `relations.schema.json`…) sera traitée dans des tickets documentaires dédiés.
