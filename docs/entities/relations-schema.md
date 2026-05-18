# Schéma des relations : relations.schema.json

`schemas/relations.schema.json` verrouille la **structure autorisée** du fichier `mvc/entities/relations.json`.

Ce fichier décrit les relations entre entités Forge : `many_to_one` et `many_to_many`. Les relations sont **séparées** des fichiers d'entités — un seul fichier `relations.json` centralise toutes les déclarations relationnelles du projet.

```
relations.schema.json   →  validation de structure (JSON Schema)
forge entity:validate    →  validation sémantique complète
                            (entités référencées existantes, cohérence des clés…)
```

Le fichier ne décrit pas directement du SQL : Forge dérive les contraintes `FOREIGN KEY`, `UNIQUE` et `INDEX` lors de la génération.

---

## Exemple minimal

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": []
}
```

`relations` peut être vide — c'est valide.

---

## Propriétés racine

| Propriété | Obligatoire | Rôle |
|---|---|---|
| `$schema` | recommandé | active l'autocomplétion et la détection d'erreurs dans VS Code |
| `schema_version` | **oui** | identifie le format canonique (`"1.0"`) |
| `relations` | **oui** | liste des relations déclarées (peut être vide) |

Les clés inconnues sont **interdites** (`additionalProperties: false`).

---

## Relation many_to_one

Une relation `many_to_one` signifie que l'entité source porte la clé étrangère vers l'entité cible. C'est la relation la plus courante (article → catégorie, commentaire → article…).

```json
{
  "type": "many_to_one",
  "from": "Article",
  "to": "Category",
  "name": "category",
  "inverse_name": "articles",
  "foreign_key": "category_id",
  "nullable": true,
  "on_delete": "restrict",
  "index": true
}
```

| Propriété | Obligatoire | Rôle |
|---|---|---|
| `type` | **oui** | toujours `"many_to_one"` |
| `from` | **oui** | entité source, propriétaire de la clé étrangère (PascalCase) |
| `to` | **oui** | entité cible pointée par la clé étrangère (PascalCase) |
| `name` | **oui** | nom logique de la relation côté source (snake_case) |
| `inverse_name` | non | nom de la relation inverse côté cible (snake_case) |
| `foreign_key` | non | nom de la colonne clé étrangère (snake_case) |
| `nullable` | non | la clé étrangère accepte NULL (défaut : `true`) |
| `on_delete` | non | comportement SQL ON DELETE |
| `index` | non | créer un index sur la clé étrangère (défaut : `true`) |

La clé étrangère est **technique** — elle n'a pas à être déclarée comme champ métier dans `fields[]` de l'entité source. Forge la génère dans la projection SQL via `relations.sql`.

---

## Relation many_to_many

Une relation `many_to_many` passe par une **table pivot** explicite. Les deux entités ne se portent pas mutuellement de clé étrangère — c'est la table pivot qui porte les deux.

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

| Propriété | Obligatoire | Rôle |
|---|---|---|
| `type` | **oui** | toujours `"many_to_many"` |
| `from` | **oui** | première entité (PascalCase) |
| `to` | **oui** | seconde entité (PascalCase) |
| `name` | **oui** | nom logique de la relation côté source (snake_case) |
| `inverse_name` | non | nom de la relation inverse côté cible (snake_case) |
| `pivot` | **oui** | définition de la table pivot |

---

## Table pivot

La table pivot est définie dans le bloc `pivot` d'une relation `many_to_many`.

| Propriété | Obligatoire | Rôle |
|---|---|---|
| `table` | **oui** | nom de la table pivot en snake_case (`article_tag`) |
| `from_key` | **oui** | colonne clé étrangère vers l'entité source (`article_id`) |
| `to_key` | **oui** | colonne clé étrangère vers l'entité cible (`tag_id`) |
| `id` | **oui** | doit valoir `true` — id technique `AUTO_INCREMENT` toujours présent |
| `unique_pair` | **oui** | doit valoir `true` — contrainte `UNIQUE (from_key, to_key)` toujours présente |
| `on_delete` | non | comportement SQL ON DELETE appliqué aux deux clés étrangères |
| `fields` | non | attributs métier supplémentaires sur la table pivot |

`pivot.id` et `pivot.unique_pair` sont contraints à `true` dans le schéma (`const: true`). Ces deux propriétés ne sont pas optionnelles — elles doivent être déclarées et valoir exactement `true`.

`pivot.fields` peut contenir des champs métier contrôlés (voir [Le JSON canonique](json-canonique.md) pour les exemples). Les noms `id`, `from_key` et `to_key` sont réservés et interdits dans `pivot.fields`.

---

## Comportement on_delete

Les valeurs autorisées dans `on_delete` (pour `many_to_one` et `pivot`) sont définies par `common.schema.json` :

| Valeur | Comportement SQL |
|---|---|
| `restrict` | interdit la suppression de la cible si des lignes source existent (recommandé par défaut) |
| `cascade` | supprime automatiquement les lignes source quand la cible est supprimée |
| `set_null` | met la clé étrangère à NULL quand la cible est supprimée |
| `no_action` | aucune action automatique (comportement dépend du moteur) |

Les valeurs sont écrites **en minuscules** dans le JSON canonique. Forge les traduit vers les formes SQL nécessaires lors de la génération.

---

## Ce qui n'est plus canonique

Ces clés appartiennent à l'ancien format legacy. Elles **ne doivent pas apparaître** dans les fichiers `schema_version: "1.0"`.

| Clé interdite | Remplacée par |
|---|---|
| `format_version` | `schema_version: "1.0"` |
| `from_entity` | `from` |
| `to_entity` | `to` |
| `foreign_key_name` | `foreign_key` |
| `source` | `from` (M2M legacy) |
| `target` | `to` (M2M legacy) |
| `pivot_table` | `pivot.table` |
| `source_key` | `pivot.from_key` |
| `target_key` | `pivot.to_key` |

Le JSON Schema bloque toute clé inconnue via `additionalProperties: false`. Un fichier utilisant `from_entity` sera rejeté dès la validation JSON Schema.

---

## Erreurs fréquentes

**Utiliser `from_entity` au lieu de `from` :**

```json
{ "type": "many_to_one", "from_entity": "Article", ... }
```

`from_entity` est une clé legacy. La clé canonique est `from`.

---

**Utiliser `to_entity` au lieu de `to` :**

```json
{ "type": "many_to_one", ..., "to_entity": "Category" }
```

La clé canonique est `to`.

---

**Oublier `schema_version` :**

```json
{ "relations": [...] }
```

`schema_version` est obligatoire. Sans elle, le fichier est invalide.

---

**Mettre `on_delete` en majuscules :**

```json
{ ..., "on_delete": "CASCADE" }
```

Les valeurs doivent être en minuscules : `cascade`, `restrict`, `set_null`, `no_action`.

---

**Déclarer une relation vers une entité inexistante :**

Le JSON Schema ne détecte pas cette incohérence — mais `forge entity:validate` la signale avec une erreur sémantique.

---

**Utiliser `many_to_many` sans bloc `pivot` :**

```json
{ "type": "many_to_many", "from": "Article", "to": "Tag", "name": "tags" }
```

`pivot` est obligatoire pour toute relation `many_to_many`.

---

**Mettre `pivot.id` ou `pivot.unique_pair` à `false` :**

```json
"pivot": { ..., "id": false, "unique_pair": false }
```

Ces deux propriétés sont contraintes à `true` par le schéma. Toute autre valeur est invalide.

---

## Valider les relations

```bash
forge entity:validate
```

Sortie humaine : liste les erreurs et avertissements pour chaque fichier d'entité et pour `relations.json`.

```bash
forge entity:validate --json
```

Sortie machine : JSON structuré avec `valid`, `errors_count`, `errors[]`.

`forge build:model`, `make:crud` et les migrations protégées utilisent ces contrats comme garde-fou — ils refusent de générer si `entity:validate` détecte des erreurs.
