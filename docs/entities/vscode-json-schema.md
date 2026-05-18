# Autocomplétion VS Code avec les schémas JSON

VS Code peut utiliser les schémas JSON Forge pour aider à remplir les fichiers
d'entités et de relations. Cette aide est optionnelle : Forge ne dépend pas de
VS Code pour valider un projet.

---

## Principe

VS Code lit un schéma JSON et, pour chaque fichier associé :

- propose les clés autorisées (autocomplétion) ;
- signale les clés inconnues ;
- propose les valeurs `enum` attendues ;
- signale les types JSON invalides.

**VS Code ne remplace pas `forge entity:validate`.** La validation structurelle
que VS Code peut apporter reste partielle ; les règles sémantiques de Forge
(entités inconnues, collisions, doublons, cohérence entre champs et index)
sont vérifiées uniquement par la CLI.

---

## Méthode 1 : utiliser `$schema` dans le fichier JSON

La façon la plus directe est d'ajouter une clé `$schema` dans chaque fichier.
Le chemin est **relatif au fichier JSON ouvert**.

### Exemple : fichier d'entité

Un fichier d'entité est typiquement placé à :

```
mvc/entities/article/article.json
```

Déclarer le schéma dans ce fichier :

```json
{
  "$schema": "../../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Article",
  "table": "articles",
  "fields": [
    {
      "name": "title",
      "type": "string",
      "max_length": 255,
      "required": true
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

Le chemin `../../../schemas/entity.schema.json` remonte trois niveaux depuis
`mvc/entities/article/` jusqu'à la racine du projet.

### Exemple : `relations.json`

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": []
}
```

Le chemin `../../schemas/relations.schema.json` remonte deux niveaux depuis
`mvc/entities/`.

---

## Méthode 2 : associer les schémas dans `.vscode/settings.json`

L'association globale évite de modifier chaque fichier JSON. Elle se place dans
`.vscode/settings.json` à la racine du projet.

### Configuration de base

```json
{
  "json.schemas": [
    {
      "fileMatch": [
        "/mvc/entities/relations.json"
      ],
      "url": "./schemas/relations.schema.json"
    },
    {
      "fileMatch": [
        "/mvc/entities/**/*.json"
      ],
      "url": "./schemas/entity.schema.json"
    }
  ]
}
```

> **Note** : si `relations.json` correspond aussi au motif `/mvc/entities/**/*.json`,
> l'entrée spécifique à `relations.json` doit rester **avant** l'entrée générique.
> L'ordre des entrées dans `json.schemas` détermine quelle association prend effet.

### Variante prudente (sous-dossiers)

Pour cibler explicitement les entités dans des sous-dossiers et éviter de
sélectionner `relations.json` via le motif générique :

```json
{
  "json.schemas": [
    {
      "fileMatch": [
        "/mvc/entities/relations.json"
      ],
      "url": "./schemas/relations.schema.json"
    },
    {
      "fileMatch": [
        "/mvc/entities/*/*.json"
      ],
      "url": "./schemas/entity.schema.json"
    }
  ]
}
```

Le motif `/mvc/entities/*/*.json` cible les entités dans des sous-dossiers :

```
mvc/entities/article/article.json   ✓
mvc/entities/media/media.json       ✓
mvc/entities/relations.json         ✗  (non ciblé — couvert par l'entrée précédente)
```

> Ce ticket documente la configuration, mais ne crée pas de fichier
> `.vscode/settings.json` dans le dépôt. La création d'une configuration
> VS Code prête à l'emploi pourra être décidée dans un ticket DX séparé.

---

## Ce que VS Code peut détecter

Avec un schéma associé, VS Code peut signaler :

| Cas | Exemple invalide | Exemple valide |
|-----|-----------------|----------------|
| Clé inconnue | `"couleur": "rouge"` dans une entité | — |
| Clé obligatoire manquante | entité sans `name` | `"name": "Article"` |
| Type JSON invalide | `"required": "oui"` | `"required": true` |
| Type Forge non autorisé | `"type": "VARCHAR(255)"` | `"type": "string"` |
| Valeur `enum` invalide | `"on_delete": "CASCADE"` | `"on_delete": "cascade"` |
| Pivot incomplet | `many_to_many` sans `pivot.table` | avec `"table": "article_tag"` |
| `unique_pair` incorrect | `"unique_pair": false` | `"unique_pair": true` |

---

## Ce que VS Code ne remplace pas

VS Code valide principalement la **structure** des fichiers JSON. `forge entity:validate`
valide en plus les **règles sémantiques** que le JSON Schema ne peut pas exprimer :

- relation vers une entité inexistante dans `mvc/entities/` ;
- doublon de table entre deux entités ;
- index pointant vers un champ absent de `fields[]` ;
- relation `many_to_many` déclarée deux fois en inverse ;
- collision entre `pivot.fields[]` et les noms réservés `from_key` / `to_key` ;
- cohérence complète avec les générateurs Forge (`build:model`, `make:crud`).

La commande officielle de diagnostic reste :

```bash
python forge.py entity:validate
```

---

## Schémas Forge concernés

| Schéma | Rôle |
|--------|------|
| `schemas/entity.schema.json` | structure d'une entité |
| `schemas/field.schema.json` | structure d'un champ métier |
| `schemas/relations.schema.json` | structure de `relations.json` |
| `schemas/pivot.schema.json` | structure d'une table pivot |
| `schemas/common.schema.json` | définitions partagées (réutilisées par les autres schémas) |

Les schémas sont autonomes : Forge n'a pas besoin d'Internet pour valider un
projet. Les `$id` commençant par `https://forge-mvc.dev/` sont des identifiants
logiques, pas des URL résolues en ligne.

---

## Compatibilité JSON Schema

Les schémas Forge déclarent **JSON Schema Draft 2020-12**.

Selon la version de VS Code et de son moteur JSON intégré, certaines règles
avancées (comme `$dynamicRef` ou certains mots-clés d'annotation) peuvent être
plus ou moins bien prises en compte. La validation officielle reste donc
`forge entity:validate`.

En pratique, les règles de base — types, `enum`, propriétés requises,
`additionalProperties: false` — sont bien reconnues par les versions récentes
de VS Code.
