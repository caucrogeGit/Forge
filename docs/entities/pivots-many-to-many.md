# Tables pivot many-to-many

Une relation `many_to_many` dans Forge passe par une **table pivot** explicite. Cette table relie deux entités sans que l'une ou l'autre ne porte de clé étrangère directe vers l'autre.

La table pivot est :

- déclarée dans `mvc/entities/relations.json`, dans le bloc `pivot` d'une relation `many_to_many` ;
- **générée par Forge** dans `relations.sql` via `forge build:model` ;
- **non déclarée comme entité classique** — elle n'a pas de fichier `<entité>.json` propre ;
- extensible avec des attributs métier contrôlés via `pivot.fields[]`.

---

## Exemple sans attribut métier

La forme minimale d'un pivot — deux entités reliées sans information supplémentaire :

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

`fields: []` est valide — aucun attribut métier n'est obligatoire.

---

## Exemple avec attributs métier

Un pivot peut porter des informations propres à la relation :

```json
{
  "type": "many_to_many",
  "from": "User",
  "to": "Project",
  "name": "projects",
  "pivot": {
    "table": "project_user",
    "from_key": "user_id",
    "to_key": "project_id",
    "id": true,
    "unique_pair": true,
    "on_delete": "cascade",
    "fields": [
      {
        "name": "role",
        "type": "string",
        "max_length": 50,
        "required": true
      },
      {
        "name": "joined_at",
        "type": "datetime",
        "nullable": true
      }
    ]
  }
}
```

`role` et `joined_at` sont des attributs **de la relation** — pas des champs des entités `User` ou `Project`.

---

## Propriétés du pivot

| Propriété | Obligatoire | Rôle |
|---|---|---|
| `table` | **oui** | nom de la table pivot en snake_case (`article_tag`) |
| `from_key` | **oui** | colonne clé étrangère vers l'entité `from` (`article_id`) |
| `to_key` | **oui** | colonne clé étrangère vers l'entité `to` (`tag_id`) |
| `id` | **oui** | doit valoir `true` — id technique `AUTO_INCREMENT` toujours présent |
| `unique_pair` | **oui** | doit valoir `true` — contrainte `UNIQUE (from_key, to_key)` toujours présente |
| `on_delete` | non | comportement SQL ON DELETE sur les deux FK (`restrict`, `cascade`, `set_null`, `no_action`) |
| `fields` | non | attributs métier de la table pivot (types Forge, mêmes règles que `field.schema.json`) |

---

## Pourquoi un id technique ?

Forge impose un `id INT NOT NULL AUTO_INCREMENT` sur toutes les tables pivot. Ce choix est délibéré :

- **extensibilité** — si la relation doit porter des attributs métier, l'`id` technique est déjà là ;
- **homogénéité** — toutes les tables générées par Forge ont la même structure de clé primaire ;
- **références externes** — un `id` stable permet de référencer une ligne pivot depuis d'autres tables ou API ;
- **évolution sans migration destructive** — transformer un pivot sans attributs en pivot avec attributs ne nécessite pas de changer la clé primaire.

Le couple `from_key / to_key` reste **unique** grâce à `unique_pair: true`. Les deux décisions coexistent et se complètent.

---

## Contrainte unique sur la paire

`unique_pair: true` ajoute une contrainte `UNIQUE (from_key, to_key)` sur la table pivot. Elle empêche de créer deux fois la même association.

Exemple : un même article ne peut pas être associé deux fois au même tag dans `article_tag`.

Cette contrainte est distincte de l'`id` technique — l'`id` identifie la ligne, la contrainte unique protège la cohérence de la relation.

`unique_pair` est contraint à `true` dans `pivot.schema.json` (`const: true`). Toute autre valeur est invalide.

---

## Attributs métier de pivot

`pivot.fields[]` permet d'ajouter des informations portées par la relation elle-même.

Exemples courants :

- rôle d'un utilisateur dans un projet (`role: string`) ;
- date d'entrée dans une équipe (`joined_at: datetime`) ;
- ordre d'affichage d'un élément dans une liste (`position: integer`) ;
- statut d'une association (`status: string`, `choices: [...]`).

Les champs pivot utilisent les **types Forge** autorisés par `field.schema.json` : `string`, `text`, `integer`, `big_integer`, `float`, `decimal`, `boolean`, `date`, `datetime`, `email`, `password`, `json`.

Les clés optionnelles sont les mêmes que pour les champs d'entité : `required`, `nullable`, `unique`, `max_length`, `precision`, `scale`, `default`, `choices`…

La règle nullable / required est la même que pour les `fields[]` d'entité (ADR-013) :
un champ `pivot.fields[]` est **nullable par défaut**. `required: true` rend le champ `NOT NULL`
et est prioritaire sur `nullable: true`.

---

## Noms réservés dans pivot.fields[]

`pivot.fields[]` ne peut pas redéclarer les colonnes techniques gérées par Forge :

- `id` — clé primaire technique
- la valeur de `from_key` (ex : `article_id`)
- la valeur de `to_key` (ex : `tag_id`)

Exemple interdit si `"from_key": "article_id"` :

```json
{
  "name": "article_id",
  "type": "integer"
}
```

`forge entity:validate` détecte cette collision et lève une erreur avec le code `FORGE_PIVOT_RESERVED_FIELD`.

---

## Projection SQL générée

`forge build:model` génère la table pivot dans `mvc/entities/relations.sql`.

**Pivot sans attribut métier** (`article_tag`) :

```sql
CREATE TABLE IF NOT EXISTS article_tag (
    id INT NOT NULL AUTO_INCREMENT,
    article_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_article_tag (article_id, tag_id),
    INDEX idx_article_tag_article_id (article_id),
    INDEX idx_article_tag_tag_id (tag_id),
    CONSTRAINT fk_article_tag_article_id
        FOREIGN KEY (article_id)
        REFERENCES article (id)
        ON DELETE cascade,
    CONSTRAINT fk_article_tag_tag_id
        FOREIGN KEY (tag_id)
        REFERENCES tag (id)
        ON DELETE cascade
);
```

**Pivot avec attributs métier** (`project_user` avec `role` et `joined_at`) :

```sql
CREATE TABLE IF NOT EXISTS project_user (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    joined_at DATETIME NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_user (user_id, project_id),
    INDEX idx_project_user_user_id (user_id),
    INDEX idx_project_user_project_id (project_id),
    CONSTRAINT fk_project_user_user_id
        FOREIGN KEY (user_id)
        REFERENCES user (id)
        ON DELETE cascade,
    CONSTRAINT fk_project_user_project_id
        FOREIGN KEY (project_id)
        REFERENCES project (id)
        ON DELETE cascade
);
```

Le SQL est une **projection générée** depuis `relations.json`. Ne pas le modifier manuellement — il sera écrasé à la prochaine exécution de `build:model`.

---

## Générer un sous-CRUD Pivot advanced

Quand un pivot porte des attributs métier (`position`, `note`, `role`…), un sous-CRUD
relationnel dédié peut être généré avec :

```bash
python forge.py make:pivot-crud Article tags
python forge.py make:pivot-crud Article tags --dry-run
```

La commande :

- charge `mvc/entities/relations.json` ;
- vérifie que la relation `Article.tags` est `many_to_many` avec `pivot.fields[]` non vide ;
- génère `mvc/controllers/pivot/article_tags_pivot_controller.py` ;
- génère `mvc/templates/pivot/article_tags/index.html` et `form.html` ;
- n'écrase pas les fichiers existants ;
- affiche les routes à ajouter manuellement dans `mvc/routes.py`.

Elle ne modifie pas `make:crud` et ne branche pas automatiquement les routes.

---

## Pivot advanced — attributs métier complets

Quand un pivot porte des attributs métier significatifs (`position`, `note`,
`role`…) et que `make:crud` est insuffisant ou bloqué, consultez la
documentation dédiée :

**[Pivot advanced — tables pivot avec attributs](pivot-advanced.md)**

Elle couvre la déclaration du contrat, la génération du sous-CRUD avec
`make:pivot-crud`, l'utilisation de `PivotAdvancedService` et la gestion
des erreurs UX.

---

## Limites actuelles

- Les attributs pivot sont validés par `forge entity:validate` et générés en SQL.
- `make:crud` **refuse** de générer le CRUD si un champ pivot est `required: true` ou
  `nullable: false`. Ces champs sont `NOT NULL` en base mais ne peuvent pas être renseignés
  par la synchronisation d'IDs générée. Pour utiliser ces champs, rendez-les nullable ou
  utilisez un module CRUD pivot dédié (voir ticket `PIVOT-CRUD-004`).
- Le CRUD avancé pour créer, modifier ou supprimer des lignes pivot avec attributs n'est
  pas encore couvert par `make:crud` — les vues générées traitent la relation mais pas les
  attributs supplémentaires.
- `forge entity:validate` reste la validation officielle avant toute génération.
