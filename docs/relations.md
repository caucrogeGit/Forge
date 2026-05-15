# Relations entre entités

Forge utilise un fichier global `mvc/entities/relations.json` pour décrire les relations entre entités. Ce fichier complète les JSON d'entités : les champs restent dans chaque entité, tandis que les liens entre entités sont centralisés et projetés vers un SQL explicite.

Cette page documente le système de relations de Forge. Le format de fichier est versionné via la clé `format_version` dans `relations.json` (actuellement `1`).

## Principe d'architecture

Les entités restent dans `mvc/entities/`, chacune avec son JSON canonique et ses fichiers générés. Les relations globales restent dans `mvc/entities/relations.json`, puis Forge génère `mvc/entities/relations.sql`.

Forge ne fournit pas d'ORM. Le SQL généré reste visible, lisible et modifiable dans l'application. Les relations décrivent des contraintes et des intentions de modèle, mais elles ne créent pas de navigation objet automatique.

`core/` doit rester générique. Il ne doit pas contenir de logique métier relationnelle, ni de relations propres à une application précise. Les choix métier appartiennent aux applications générées, aux starters ou aux modules générateurs.

## Format version 1

Le format version 1 de `relations.json` contient une version et une liste de relations.

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "contact_ville",
      "type": "many_to_one",
      "from_entity": "Contact",
      "to_entity": "Ville",
      "from_field": "ville_id",
      "to_field": "id",
      "foreign_key_name": "fk_contact_ville",
      "on_delete": "SET NULL",
      "on_update": "CASCADE"
    }
  ]
}
```

| Clé | Rôle |
| --- | --- |
| `format_version` | Version du format relationnel. La valeur attendue est `1`. |
| `relations` | Liste des relations globales. |
| `name` | Nom logique de la relation. |
| `type` | Type de relation. La version 1 du format supporte `many_to_one` et `many_to_many` côté SQL. |
| `from_entity` | Entité source, celle qui porte la clé étrangère. |
| `to_entity` | Entité cible, celle qui porte la clé primaire référencée. |
| `from_field` | Champ source dans le JSON d'entité, côté clé étrangère. |
| `to_field` | Champ cible dans le JSON d'entité, côté clé primaire. |
| `foreign_key_name` | Nom de la contrainte SQL. |
| `on_delete` | Action SQL `ON DELETE`. |
| `on_update` | Action SQL `ON UPDATE`. |

## Exemple many_to_one

Exemple neutre : un `Contact` appartient éventuellement à une `Ville`.

Dans l'entité `Contact`, le champ `ville_id` est un champ normal, visible dans le JSON de l'entité :

```json
{
  "name": "ville_id",
  "column": "VilleId",
  "python_type": "int",
  "sql_type": "INT",
  "nullable": true,
  "primary_key": false,
  "auto_increment": false,
  "constraints": {}
}
```

La relation globale est ensuite décrite dans `mvc/entities/relations.json` :

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "contact_ville",
      "type": "many_to_one",
      "from_entity": "Contact",
      "to_entity": "Ville",
      "from_field": "ville_id",
      "to_field": "id",
      "foreign_key_name": "fk_contact_ville",
      "on_delete": "SET NULL",
      "on_update": "CASCADE"
    }
  ]
}
```

## SQL généré

Forge génère un fichier `relations.sql` contenant du SQL relationnel explicite :
contraintes `many_to_one` et tables pivot `many_to_many`.

```sql
ALTER TABLE contact
    ADD CONSTRAINT fk_contact_ville
    FOREIGN KEY (VilleId)
    REFERENCES ville (Id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
```

Le fichier `relations.sql` contient les contraintes globales, typiquement des
`ALTER TABLE ... ADD CONSTRAINT`, et les tables pivot déclaratives
`many_to_many`. Les `CREATE TABLE` des entités normales restent dans les
fichiers SQL des entités.

## Règles de validation

Forge valide les relations avant de générer `relations.sql`.

- Les entités `from_entity` et `to_entity` doivent exister.
- Les champs `from_field` et `to_field` doivent exister.
- `to_field` doit être une clé primaire.
- Les types Python des champs source et cible doivent être compatibles.
- Les types SQL des champs source et cible doivent être compatibles pour MariaDB.
- `SET NULL` exige que le champ source soit nullable.
- Les noms SQL, comme `foreign_key_name`, sont validés.
- Les noms de relations et de contraintes doivent rester uniques.

Ces règles évitent de générer une contrainte SQL incohérente ou dangereuse.

## Relations many_to_many déclaratives

Depuis Forge 1.5.0, une relation `many_to_many` peut être déclarée dans `relations.json`.

### Format

```json
{
  "format_version": 1,
  "relations": [
    {
      "type": "many_to_many",
      "source": "article",
      "target": "tag",
      "pivot_table": "article_tag",
      "source_key": "article_id",
      "target_key": "tag_id",
      "pivot_fields": [
        {
          "name": "position",
          "sql_type": "INT",
          "nullable": false
        },
        {
          "name": "note",
          "sql_type": "VARCHAR(255)",
          "nullable": true
        }
      ]
    }
  ]
}
```

| Clé | Rôle |
| --- | --- |
| `type` | Doit valoir `"many_to_many"`. |
| `source` | Nom de la table source (identifiant SQL, snake_case). |
| `target` | Nom de la table cible (identifiant SQL, snake_case). |
| `pivot_table` | Nom de la table pivot (identifiant SQL, snake_case). |
| `source_key` | Colonne FK vers la table source dans le pivot. |
| `target_key` | Colonne FK vers la table cible dans le pivot. |
| `pivot_fields` | Liste optionnelle de colonnes supplémentaires sur le pivot. |

Si `pivot_fields` est absent, Forge génère le même pivot simple que
REL-M2M-002.

### Règles de validation

- `type`, `source`, `target`, `pivot_table`, `source_key`, `target_key` sont tous obligatoires.
- Chaque valeur de clé relationnelle doit être une chaîne et un identifiant SQL valide.
- `pivot_fields` est optionnel.
- Si `pivot_fields` est présent, il doit être une liste.
- Chaque champ pivot exige `name` et `sql_type`.
- `nullable` est optionnel et vaut `false` par défaut.
- Un champ pivot ne peut pas dupliquer `source_key` ou `target_key`.
- Les clés inconnues sont refusées.

### SQL généré

Depuis REL-M2M-002, `forge sync:relations` génère la table pivot SQL dans
`mvc/entities/relations.sql`.

Pour l'exemple précédent, le SQL généré est :

```sql
CREATE TABLE IF NOT EXISTS article_tag (
    article_id INT NOT NULL,
    tag_id INT NOT NULL,
    position INT NOT NULL,
    note VARCHAR(255) NULL,
    PRIMARY KEY (article_id, tag_id),
    INDEX idx_article_tag_article_id (article_id),
    INDEX idx_article_tag_tag_id (tag_id),
    CONSTRAINT fk_article_tag_article_id
        FOREIGN KEY (article_id)
        REFERENCES article(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_article_tag_tag_id
        FOREIGN KEY (tag_id)
        REFERENCES tag(id)
        ON DELETE CASCADE
);
```

Les noms d'index et de contraintes sont déterministes :

- `idx_{pivot_table}_{source_key}` ;
- `idx_{pivot_table}_{target_key}` ;
- `fk_{pivot_table}_{source_key}` ;
- `fk_{pivot_table}_{target_key}`.

Les relations `many_to_many` et `many_to_one` peuvent coexister dans le même `relations.json`.

### Pivot enrichi

Depuis REL-PIVOT-001, une relation `many_to_many` peut déclarer des colonnes
supplémentaires avec `pivot_fields`. Forge les ajoute uniquement dans le SQL de
la table pivot.

Exemple complet :

```json
{
  "type": "many_to_many",
  "source": "article",
  "target": "tag",
  "pivot_table": "article_tag",
  "source_key": "article_id",
  "target_key": "tag_id",
  "pivot_fields": [
    {
      "name": "position",
      "sql_type": "INT",
      "nullable": false
    },
    {
      "name": "note",
      "sql_type": "VARCHAR(255)",
      "nullable": true
    }
  ]
}
```

SQL généré :

```sql
CREATE TABLE IF NOT EXISTS article_tag (
    article_id INT NOT NULL,
    tag_id INT NOT NULL,
    position INT NOT NULL,
    note VARCHAR(255) NULL,
    PRIMARY KEY (article_id, tag_id),
    INDEX idx_article_tag_article_id (article_id),
    INDEX idx_article_tag_tag_id (tag_id),
    CONSTRAINT fk_article_tag_article_id
        FOREIGN KEY (article_id)
        REFERENCES article(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_article_tag_tag_id
        FOREIGN KEY (tag_id)
        REFERENCES tag(id)
        ON DELETE CASCADE
);
```

Les champs pivot ne sont pas inclus dans la clé primaire composite et Forge ne
crée pas d'index automatique sur eux.

### Formulaires CRUD côté source

Depuis REL-M2M-003, `forge make:crud` exploite aussi les relations `many_to_many`
où l'entité générée est la `source`.

Pour l'exemple `article -> tag`, le formulaire `Article` généré contient un
champ conceptuellement équivalent à :

```html
<select name="tag_ids" multiple>
    <!-- options chargées depuis tag -->
</select>
```

Le nom du champ suit la convention `{target}_ids`. Le contrôleur généré charge
les choix de la table cible avec du SQL explicite :

```sql
SELECT id, name
FROM tag
ORDER BY name
```

Le champ de libellé suit la même logique que les relations `many_to_one` :
`name`, `nom`, `title`, `titre`, `label`, `libelle`, puis premier champ texte,
puis clé primaire si aucun champ texte n'existe.

À la création, Forge insère les lignes pivot sélectionnées après la création de
l'entité source :

```sql
INSERT INTO article_tag (article_id, tag_id)
VALUES (?, ?)
```

À l'édition, Forge applique une synchronisation simple et lisible :

```sql
DELETE FROM article_tag
WHERE article_id = ?

INSERT INTO article_tag (article_id, tag_id)
VALUES (?, ?)
```

Seul le côté source est traité dans ce ticket. Le CRUD `Tag` ne reçoit pas
automatiquement un champ inverse vers les articles.

### Affichage CRUD côté source

Depuis REL-M2M-004, `forge make:crud` affiche aussi les libellés liés dans les
pages `index.html` et `show.html` générées pour l'entité source.

Pour `article -> tag`, la liste peut afficher une colonne `Tag` :

| Titre | Tag | Actions |
| --- | --- | --- |
| Article 1 | Python, Web | Voir / Modifier / Supprimer |

Le contrôleur de liste charge les libellés en une requête groupée sur les ids
affichés :

```sql
SELECT
    pivot.article_id AS source_id,
    tag.id AS target_id,
    tag.name AS target_label
FROM article_tag pivot
JOIN tag ON tag.id = pivot.tag_id
WHERE pivot.article_id IN (...)
ORDER BY tag.name
```

La fiche `show` charge seulement les libellés de l'objet affiché :

```sql
SELECT tag.id AS target_id, tag.name AS target_label
FROM article_tag pivot
JOIN tag ON tag.id = pivot.tag_id
WHERE pivot.article_id = ?
ORDER BY tag.name
```

L'affichage reste volontairement simple : libellés séparés par des virgules,
état vide lisible, aucun lien automatique vers les fiches cible. Les formulaires
create/edit et la synchronisation pivot restent ceux de REL-M2M-003.

### Relations ordonnées (`order_column`)

Depuis REL-ORDERED-001, une relation `many_to_many` peut déclarer un champ pivot
comme colonne de tri via `order_column`. Quand ce champ est présent, les requêtes
`list` et `show` générées par `make:crud` trient les libellés liés selon ce champ
plutôt que par le libellé de la cible.

Règles :

- `order_column` est optionnel.
- Sa valeur doit être un identifiant SQL valide.
- Il doit être le nom d'un champ déclaré dans `pivot_fields` de la même relation.

Exemple :

```json
{
  "type": "many_to_many",
  "source": "article",
  "target": "tag",
  "pivot_table": "article_tag",
  "source_key": "article_id",
  "target_key": "tag_id",
  "pivot_fields": [
    { "name": "position", "sql_type": "INT", "nullable": false }
  ],
  "order_column": "position"
}
```

SQL généré (liste) :

```sql
SELECT pivot.article_id AS source_id,
       tag.id AS target_id,
       tag.name AS target_label
FROM article_tag pivot
JOIN tag ON tag.id = pivot.tag_id
WHERE pivot.article_id IN (...)
ORDER BY pivot.position
```

Sans `order_column`, l'ordre reste par défaut sur le libellé de la cible
(`ORDER BY tag.name`). `order_column` ne modifie pas le SQL `CREATE TABLE`
généré par `sync:relations`.

---

## Limites actuelles

Le système de relations ne supporte pas encore directement :

- `one_to_many` exploité dans le CRUD généré ;
- relation principale ;
- génération automatique de `JOIN` arbitraires au-delà des relations déjà supportées ;
- gestion inverse côté cible ;
- liens automatiques vers les fiches cible ;
- autocomplete, tags UI ou interaction HTMX spécifique ;
- saisie, édition ou affichage des champs `pivot_fields` dans le CRUD ;
- attach/detach applicatif dédié aux pivots enrichis.

Depuis Forge 1.2.0, `forge make:crud` génère automatiquement un `<select>` pour les champs FK déclarés dans `relations.json` — voir la section *Exploitation dans le CRUD généré* ci-dessous.

## Pivot explicite

Un many-to-many peut déjà être modélisé manuellement avec une entité pivot normale et deux relations `many_to_one`.

Exemple neutre :

- `Article`
- `Tag`
- `ArticleTag`

`ArticleTag` est une entité associative classique :

```json
{
  "entity": "ArticleTag",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "article_id", "sql_type": "INT" },
    { "name": "tag_id", "sql_type": "INT" }
  ]
}
```

Les deux relations sont ensuite déclarées dans `relations.json` :

```json
{
  "format_version": 1,
  "relations": [
    {
      "name": "article_tag_article",
      "type": "many_to_one",
      "from_entity": "ArticleTag",
      "to_entity": "Article",
      "from_field": "article_id",
      "to_field": "id",
      "foreign_key_name": "fk_article_tag_article",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    },
    {
      "name": "article_tag_tag",
      "type": "many_to_one",
      "from_entity": "ArticleTag",
      "to_entity": "Tag",
      "from_field": "tag_id",
      "to_field": "id",
      "foreign_key_name": "fk_article_tag_tag",
      "on_delete": "CASCADE",
      "on_update": "CASCADE"
    }
  ]
}
```

Cette approche garde le modèle explicite : le pivot est une vraie entité, avec son propre SQL et son propre CRUD si nécessaire.

## Exploitation dans le CRUD généré

Forge 1.2.0 commence à exploiter les relations `many_to_one` dans le CRUD généré.
Depuis REL-M2M-003, le CRUD généré exploite aussi les relations `many_to_many`
côté source dans les formulaires create/edit.
Depuis REL-M2M-004, les mêmes relations sont affichées côté source dans les
listes et les fiches détail générées.

Quand l'entité générée est le `from_entity` d'une relation, le champ FK correspondant peut être rendu comme un choix applicatif :

- le formulaire Python utilise `RelationField`, qui hérite de `ChoiceField` ;
- la vue `form.html` utilise un `<select>` ;
- le contrôleur fournit les choix au formulaire ;
- le modèle généré charge les choix depuis la table cible avec du SQL visible.

Comme `relations.json` (version 1 du format) ne contient pas encore de `label_field`, Forge choisit le libellé affiché avec un fallback simple :

1. premier champ texte non-PK de l'entité cible ;
2. sinon clé primaire cible.

Le support `many_to_many` reste limité au côté source, aux formulaires simples,
à la synchronisation simple des pivots et à l'affichage texte des libellés.
`pivot_fields` enrichit seulement le SQL généré. Il ne crée pas de navigation
objet, pas de liens automatiques vers les cibles et pas d'ORM.

## Ce qui reste à venir

Les prochains incréments relationnels prévus :

- relations ordonnées ;
- `label_field` explicite dans une version future du format `relations.json` ;
- navigation objet optionnelle sans ORM complet.

Forge conserve sa doctrine : pas d'ORM, SQL visible, incréments génériques dans les générateurs.

## Bonnes pratiques

- Nommez explicitement les relations, par exemple `contact_ville` ou `article_categorie`.
- Nommez clairement les contraintes SQL, par exemple `fk_contact_ville`.
- Préférez des champs FK explicites comme `ville_id`, `categorie_id` ou `auteur_id`.
- Ne cachez pas une vraie entité métier dans un pivot trop complexe.
- Utilisez une entité associative quand le pivot porte beaucoup de données.
- Gardez les relations génériques dans `relations.json` et les règles métier dans l'application.
