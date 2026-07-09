# Déclarer une entité avec `make:entity`

Objectif : créer le contrat JSON d'une première entité `Article`.

**Ce que vous allez apprendre :** `forge make:entity` génère un fichier de contrat dans `mvc/entities/`, puis vous complétez ses champs.
La commande ne réécrit jamais un fichier existant : elle crée, vous éditez.

!!! note "Forge génère, vous éditez"
    `make:entity` produit un squelette de contrat.
    Les champs métier se déclarent ensuite à la main dans le JSON : c'est votre dictionnaire de données, versionné.

## Générer le contrat

```bash
forge make:entity Article
```

Forge crée `mvc/entities/article/article.json` avec la structure canonique minimale.

## Compléter les champs

Ouvrez le contrat et déclarez les champs de l'article.

```json
{
  "schema_version": "1.0",
  "name": "Article",
  "table": "article",
  "fields": [
    { "name": "title", "type": "string", "max_length": 255, "required": true },
    { "name": "content", "type": "text", "nullable": true },
    { "name": "published", "type": "boolean", "default": false }
  ]
}
```

Chaque champ porte au minimum un `name` (snake_case) et un `type` Forge.
Les options (`required`, `nullable`, `max_length`, `default`, `unique`…) restent explicites et lisibles.

## Valider le contrat

```bash
forge entity:validate
```

`entity:validate` vérifie la forme du contrat et la cohérence sémantique avant toute génération.
Un contrat invalide est refusé ici, pas au moment de générer la base.

## Commandes Forge utilisées

| Commande | Rôle dans ce palier | Référence |
|---|---|---|
| `forge make:entity Article` | Créer le contrat de l'entité `Article`. | [make:entity](../../modules/make_entity.md) |
| `forge entity:validate` | Valider forme et sémantique des contrats. | [entity:validate](../../modules/entity_validate.md) |

## La suite

Votre entité est déclarée et valide.
Au palier suivant, vous la reliez à une autre entité avec `forge make:relation`.

[Continuer : relier deux entités](relation-make.md)
