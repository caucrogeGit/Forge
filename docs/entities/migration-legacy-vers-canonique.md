# Convertir un ancien projet Forge vers le JSON canonique

!!! danger "Le format legacy est refusé"
    Le format `format_version: 1` n'est plus accepté. `build:model` et `make:crud` lèvent
    une erreur si un fichier d'entité ou de relations utilise l'ancien format.
    Ce guide sert à convertir manuellement les anciens fichiers avant utilisation.

Ce guide s'adresse aux projets dont les fichiers JSON utilisent encore l'ancien format
(`format_version: 1`). Il explique la conversion manuelle vers le format canonique
(`schema_version: "1.0"`), désormais obligatoire. Il ne modifie pas le core Forge.

---

## 1. Diagnostiquer un projet legacy

Rechercher les fichiers legacy dans votre projet :

```bash
grep -RInE 'format_version|sql_type|python_type|primary_key|auto_increment|from_entity|to_entity|foreign_key_name' mvc/entities
```

Si des occurrences apparaissent, les fichiers concernés sont en format legacy et doivent
être migrés.

Vérifier ensuite avec la validation canonique :

```bash
python forge.py entity:validate
```

`entity:validate` valide le format canonique (`schema_version: "1.0"`) via JSON Schema.
Un fichier legacy ne passe pas cette validation — c'est attendu et normal avant migration.

---

## 2. Migrer une entité

### Avant — format legacy

```json
{
  "format_version": 1,
  "entity": "Contact",
  "table": "contacts",
  "fields": [
    {
      "name": "contact_id",
      "sql_type": "INT",
      "python_type": "int",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(80)",
      "python_type": "str",
      "nullable": false,
      "constraints": {
        "max_length": 80
      }
    },
    {
      "name": "email",
      "sql_type": "VARCHAR(120)",
      "python_type": "str",
      "nullable": true,
      "constraints": {
        "max_length": 120
      }
    }
  ]
}
```

### Après — format canonique

```json
{
  "$schema": "../../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Contact",
  "table": "contacts",
  "fields": [
    {
      "name": "nom",
      "type": "string",
      "max_length": 80,
      "nullable": false
    },
    {
      "name": "email",
      "type": "string",
      "max_length": 120,
      "nullable": true
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

### Ce qui change

| Avant (legacy) | Après (canonique) |
|---|---|
| `format_version: 1` | `schema_version: "1.0"` |
| `entity: "Contact"` | `name: "Contact"` |
| Champ `contact_id` (PK explicite) | **Supprimé** — Forge génère `Id` automatiquement |
| `sql_type: "VARCHAR(80)"` | `type: "string"` |
| `python_type: "str"` | **Supprimé** — dérivé automatiquement |
| `primary_key: true` | **Supprimé** |
| `auto_increment: true` | **Supprimé** |
| `constraints: { max_length: 80 }` | `max_length: 80` (propriété directe) |
| Absent | `"$schema"` (lien vers le contrat JSON Schema) |
| Absent | `"options"` (timestamps, soft_delete) |

---

## 3. Table de correspondance des types

| Legacy (`sql_type`) | Canonique (`type`) | Paramètres supplémentaires |
|---|---|---|
| `VARCHAR(n)` | `string` | `max_length: n` |
| `TEXT` | `text` | — |
| `INT` / `BIGINT` | `integer` | — |
| `BOOLEAN` / `TINYINT(1)` | `boolean` | — |
| `DATE` | `date` | — |
| `DATETIME` / `TIMESTAMP` | `datetime` | — |
| `DECIMAL(p, s)` | `decimal` | `precision: p, scale: s` |
| `VARCHAR(n)` (mot de passe) | `password` | `max_length: n` |

Les types `python_type` (`str`, `int`, `bool`, etc.) sont tous supprimés — Forge les dérive
automatiquement du type canonique lors de la génération.

---

## 4. Cas des anciennes clés primaires

### PK technique (`*Id`)

Dans les anciens projets, la clé primaire était souvent nommée `ContactId`, `UtilisateurId`,
`VilleId`, etc. Dans le format canonique, Forge génère une colonne technique `Id`
automatiquement — elle n'est pas à déclarer dans les champs.

**Si du code applicatif référence l'ancienne PK, il doit être mis à jour** :

```python
# Avant
row["ContactId"]
row["UtilisateurId"]

# Après
row["Id"]
```

Rechercher dans le code applicatif :

```bash
grep -RInE 'row\["\w+Id"\]|utilisateur\["\w+Id"\]|contact\["\w+Id"\]' mvc/
```

### FK métier (`ville_id`, `cours_id`, etc.)

Les colonnes qui sont des **clés étrangères métier** (ex. `ville_id`, `cours_id`) ne sont
**pas** la PK de l'entité — elles restent dans les champs et ne changent pas de nom.

```json
{ "name": "ville_id", "type": "integer", "nullable": true }
```

La colonne générée reste `ville_id`. Le code applicatif `row["ville_id"]` n'a pas besoin
d'être modifié.

---

## 5. Migrer `relations.json`

### Avant — format legacy

```json
{
  "format_version": 1,
  "relations": [
    {
      "type": "many_to_one",
      "from_entity": "Contact",
      "to_entity": "Ville",
      "foreign_key_name": "ville_id",
      "on_delete": "CASCADE"
    }
  ]
}
```

### Après — format canonique

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_one",
      "from": "Contact",
      "to": "Ville",
      "name": "ville",
      "foreign_key": "ville_id",
      "nullable": true,
      "on_delete": "set_null",
      "index": true
    }
  ]
}
```

### Ce qui change

| Avant (legacy) | Après (canonique) |
|---|---|
| `from_entity` | `from` |
| `to_entity` | `to` |
| `foreign_key_name` | `foreign_key` |
| `on_delete: "CASCADE"` | `on_delete: "cascade"` (minuscules) |
| Absent | `name` (nom de la relation, requis) |
| Absent | `nullable` (requis) |
| Absent | `index` (optionnel) |

Les valeurs `on_delete` canoniques sont en minuscules : `cascade`, `set_null`, `restrict`,
`no_action`.

---

## 6. Migrer une relation many-to-many

Le format canonique `many_to_many` utilise un bloc `pivot` explicite. Les anciennes clés
`pivot_table`, `source_key`, `target_key` n'existent pas en canonique.

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": [
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
  ]
}
```

Le bloc `pivot` déclare explicitement la table de jointure, les deux clés étrangères,
et les éventuels attributs métier dans `fields[]`.

---

## 7. Limites de la migration manuelle

- **`default`** : les valeurs par défaut SQL peuvent ne pas être représentées dans tous
  les types canoniques. Vérifier la documentation du type ciblé.
- **Section `media`** : la clé racine `media` n'est pas supportée par le JSON Schema
  canonique. Elle doit être supprimée ou transformée en champs métier séparés.
- **`min` / `max`** : ces contraintes sont validées par le JSON Schema mais ne génèrent
  pas forcément de contrainte `CHECK` SQL dans la version actuelle.
- **`nullable`** : à vérifier pour chaque champ — la valeur par défaut peut différer
  entre legacy et canonique.
- **Code applicatif** : les modèles, contrôleurs et vues qui référencent des colonnes
  supprimées (ex. l'ancienne PK) doivent être mis à jour manuellement.
- **Outil automatique** : aucun outil de migration automatique n'est fourni.
  Si ce besoin devient prioritaire, voir le ticket `LEGACY-MIGRATION-TOOL-001`.

---

## 8. Valider après migration

Après conversion des fichiers, exécuter dans l'ordre :

```bash
# Vérifier le contrat JSON canonique
python forge.py entity:validate

# Vérifier la projection SQL/Python
python forge.py build:model

# Vérifier la santé des schémas
python forge.py schema:doctor

# Lancer la suite de tests
pytest
```

`entity:validate` signale toute violation du contrat JSON Schema.

`build:model` confirme que le pipeline de génération accepte les nouvelles entités
et produit des fichiers SQL et Python cohérents.

Les tests applicatifs doivent confirmer que les modèles, contrôleurs et vues ne
référencent plus d'anciennes colonnes supprimées (ex. l'ancienne PK renommée `Id`).

---

## Références

- Format canonique : [Le JSON canonique](json-canonique.md)
- Schéma des entités : [Schéma des entités](entity-schema.md)
- Schéma des relations : [Schéma des relations](relations-schema.md)
- Types Forge : [Types Forge vers MariaDB](types-forge-mariadb.md)
- Tables pivot : [Tables pivot many-to-many](pivots-many-to-many.md)
- Politique de dépréciation : ADR-012 `docs/adr/012-legacy-format-deprecation-policy.md`
