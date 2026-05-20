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
    },
    {
      "fileMatch": [
        "/mvc/security/rbac.json"
      ],
      "url": "./schemas/rbac.schema.json"
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

Cette configuration est disponible dans `.vscode/settings.json` à la racine du dépôt.
Elle est automatiquement prise en compte dès l'ouverture du projet dans VS Code.

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

Les commandes officielles de validation restent :

```bash
python forge.py schema:doctor       # vérifie l'intégrité du registre de schémas
python forge.py entity:validate     # validation sémantique des entités et relations
python forge.py rbac:validate       # validation du contrat RBAC (optionnel)
```

---

## Schémas Forge concernés

| Schéma | Rôle |
|--------|------|
| `schemas/entity.schema.json` | structure d'une entité |
| `schemas/field.schema.json` | structure d'un champ métier |
| `schemas/relations.schema.json` | structure de `relations.json` |
| `schemas/pivot.schema.json` | structure d'une table pivot |
| `schemas/rbac.schema.json` | structure de `mvc/security/rbac.json` |
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

---

## Exemple de fichiers couverts

La configuration `.vscode/settings.json` couvre les chemins suivants dans un projet Forge :

| Fichier | Schéma associé |
|---------|----------------|
| `mvc/entities/article/article.json` | `schemas/entity.schema.json` |
| `mvc/entities/user/user.json` | `schemas/entity.schema.json` |
| `mvc/entities/media/media.json` | `schemas/entity.schema.json` |
| `mvc/entities/relations.json` | `schemas/relations.schema.json` |
| `mvc/security/rbac.json` | `schemas/rbac.schema.json` |

**Non couverts automatiquement** (utiliser `$schema` explicite) :

- fichiers JSON hors de `mvc/` ;
- fichiers JSON dans `starters/` ou `examples/` ;
- `schemas/*.schema.json` eux-mêmes.

---

## Commandes Forge complémentaires

VS Code aide à l'édition, mais ne remplace pas les commandes de validation Forge :

| Commande | Ce qu'elle vérifie |
|----------|-------------------|
| `python forge.py schema:doctor` | intégrité du registre de schémas, références locales |
| `python forge.py entity:validate` | cohérence sémantique des entités et relations |
| `python forge.py rbac:validate` | contrat RBAC (optionnel) |
| `python forge.py build:model` | génération SQL et modèles depuis les entités |

Ces commandes vérifient des règles que le JSON Schema ne peut pas exprimer :

- relation vers une entité inexistante dans `mvc/entities/` ;
- doublon de table entre deux entités ;
- collision entre `pivot.fields[]` et les noms réservés ;
- cohérence métier RBAC (rôles/permissions croisés) ;
- génération effective des artefacts SQL et Python.

---

## Dépannage

### VS Code ne signale pas d'erreur dans un fichier JSON Forge

1. Vérifier que le dossier ouvert dans VS Code est **la racine du projet Forge**
   (celui qui contient `mvc/`, `schemas/`, `.vscode/`).
2. Vérifier que `.vscode/settings.json` existe et contient `json.schemas`.
3. Vérifier que les schémas existent : `schemas/entity.schema.json`, etc.
   → `python forge.py schema:doctor`
4. Recharger la fenêtre VS Code : `Ctrl+Shift+P` → `Developer: Reload Window`.

### VS Code signale une erreur mais `entity:validate` ne trouve rien

VS Code valide la structure JSON Schema. Certaines erreurs structurelles sont
détectables uniquement par le schéma (ex : clé inconnue, type incorrect).
Si l'erreur est dans une propriété non couverte sémantiquement, elle peut
apparaître dans VS Code mais pas dans `entity:validate`, ou inversement.

Les deux outils sont complémentaires — utiliser les deux.

### Le schéma RBAC n'est pas reconnu dans VS Code

Le fichier `mvc/security/rbac.json` est optionnel. S'il n'existe pas,
VS Code n'a rien à valider. S'il existe et que VS Code ne l'associe pas,
vérifier que le chemin exact est `mvc/security/rbac.json`
(pas `mvc/security/rbac.schema.json` ou un autre nom).
