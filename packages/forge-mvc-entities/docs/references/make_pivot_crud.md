# Le générateur de sous-CRUD pivot dans Forge

Ce document décrit la déclaration d'un pivot enrichi dans `relations.json` et la commande `make:pivot-crud` qui en génère le sous-CRUD.

Le fichier de code correspondant est `forge_mvc_entities/make_pivot_crud.py`.

## 1. À quoi sert ce module ?

Le CRUD standard (`make:crud`) synchronise des paires d'IDs et ne sait pas gérer les attributs d'une association.
`make:pivot-crud` génère un contrôleur et des gabarits dédiés qui, eux, manipulent ces attributs.

C'est un générateur **opt-in** : il crée des fichiers neufs (write-if-new), ne touche pas au code existant, et ne branche **pas** les routes automatiquement.

## 2. Déclarer la relation dans `relations.json`

```json
{
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
        "fields": [
          { "name": "position", "type": "integer", "nullable": false },
          { "name": "note", "type": "string", "max_length": 120, "nullable": true }
        ]
      }
    }
  ]
}
```

Points clés :

- `schema_version: "1.0"` est obligatoire.
- un `pivot.fields[]` non vide déclenche le besoin d'un sous-CRUD dédié ;
- `make:crud` **refuse** de générer le CRUD si un champ est `required: true` ou `nullable: false`, avec un message suggérant `make:pivot-crud`.

Après modification, relancer `entity:validate` puis `build:model`.

## 3. Générer le sous-CRUD

```bash
python forge.py make:pivot-crud Article tags
python forge.py make:pivot-crud Article tags --dry-run
```

`Article` est l'entité source (`"from"`), `tags` le nom de la relation (`"name"`).

| Comportement | Description |
|---|---|
| `--dry-run` | liste les fichiers qui seraient générés, sans rien écrire |
| génération | crée les fichiers absents (write-if-new) |
| fichiers existants | préservés, jamais écrasés |
| routes | fichier dédié `mvc/routes/<src>_<relation>_pivot_routes.py` (ADR-068) ; branchement affiché, **jamais injecté** |
| `make:crud` | non modifié, reste **neutre** |

## 4. Les fichiers générés

```
mvc/controllers/pivot/article_tags_pivot_controller.py
mvc/views/app/pivot/article_tags/index.html
mvc/views/app/pivot/article_tags/form.html
mvc/routes/article_tags_pivot_routes.py
```

Les vues vivent sous le namespace applicatif `APP_VIEWS_NAMESPACE` (`app` par défaut, ADR-073) et étendent `layouts/base.html`.
Le branchement des routes (deux lignes dans `mvc/routes/__init__.py`) est affiché en fin de commande.

Le contrôleur expose six actions (`index`, `add_form`, `add`, `edit_form`, `edit`, `remove`) et importe `PivotAdvancedService`, `PivotConstraintError` et `pivot_error_to_form_error`.
Les actions `add` et `edit` convertissent les erreurs de contrainte en `PivotFormError` transmis au gabarit.
Les gabarits générés sont une base minimale, à adapter.

## 5. Commandes utiles

```bash
python forge.py entity:validate                          # valider relations.json
python forge.py build:model                              # générer le SQL pivot
python forge.py make:pivot-crud Article tags --dry-run   # prévisualiser
python forge.py make:pivot-crud Article tags             # générer
python forge.py routes:list                              # inspecter les routes
```

## 6. Voir aussi

- [Le service pivot](service.md) : l'API runtime utilisée par le contrôleur généré.
- [Vue d'ensemble Pivot advanced](../reference.md).
