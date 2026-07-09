# ADR-069 : Clé étrangère de première classe (type de champ `foreign_key`)

## Statut

Acceptée (2026-07-09).

## Contexte

Depuis l'ADR sur les relations `many_to_one` (retour terrain FORGE-12/13/14), la colonne de clé étrangère était portée par `mvc/entities/relations.sql` : `make:relation` n'écrivait que dans `relations.json`, `generate_relations_sql` émettait un `ADD COLUMN` (au type de la PK visée) suivi de la contrainte, et `make:crud` injectait un champ synthétique pour que le formulaire et le modèle gèrent la FK.

Ce modèle fonctionne de bout en bout, mais la FK n'est pas visible dans le contrat de l'entité (`classe.json` ne montre pas `annee_scolaire_id`), la chaîne applicative doit la traiter par des cas particuliers (injection synthétique dans `make:crud`, option `--with-relations` pour la migration), et le type SQL exact (`BIGINT UNSIGNED`) n'était exprimable par aucun type Forge (`big_integer` donne `BIGINT` signé).

Le retour terrain (retour-013) propose que `make:relation` **ajoute la clé étrangère comme champ de l'entité source**, pour que la FK soit un champ comme les autres et que tout l'outillage la gère uniformément.

## Décision

La clé étrangère devient un **champ de première classe** de l'entité source, via un nouveau type de champ déclaratif :

```json
{ "name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire", "required": true }
```

- Le normaliseur résout `type: foreign_key` au type de la **clé primaire visée**, c'est-à-dire `dialect.identity_type()` (`BIGINT UNSIGNED` sur MariaDB), avec `python_type: int`. Comme toutes les PK Forge sont `identity_type()`, ce type est correct quelle que soit l'entité cible, et reste backend-agnostique (ADR-054).
- La **colonne** garde le nom snake_case fidèle au dictionnaire (`annee_scolaire_id`), là où un champ ordinaire adopte une colonne PascalCase.
- `make:relation` **injecte** ce champ dans le JSON de l'entité source, de façon chirurgicale et idempotente (écriture annoncée, préserve les autres champs), en plus d'écrire la relation dans `relations.json`.
- La relation dans `relations.json` reste la source de la **contrainte** (`FOREIGN KEY`), de `on_delete`, de l'`inverse_name` et de la cardinalité. Comme la FK est désormais un champ déclaré, `relations.sql` ne pose plus que la contrainte (plus d'`ADD COLUMN`), et `make:crud` la gère naturellement (le champ synthétique n'est plus nécessaire).

## Conséquences

- Le contrat d'entité est **complet** : un lecteur de `classe.json` voit la clé étrangère (charte principe 10).
- La chaîne `sync:entity` / `build:model` génère la colonne FK dans le `.sql` de l'entité, uniformément avec les autres champs.
- `make:crud` n'a plus besoin d'injection synthétique pour une FK déclarée (l'injection subsiste comme repli pour une relation écrite sans champ).
- `make:relation` écrit dans un fichier d'entité (charte §7) : l'écriture est chirurgicale, annoncée (`[MODIFIE]`) et idempotente, à l'image de l'injection de nav par `make:auth` et de `opt-in:enable`.
- Compatibilité : une relation écrite directement dans `relations.json` sans champ FK déclaré reste supportée (l'ancien chemin `ADD COLUMN` de `relations.sql` sert alors de repli).

## Alternatives écartées

- **Garder « relations.sql porte la FK »** (modèle précédent) : fonctionnel mais laisse la FK hors du contrat, impose l'injection synthétique et un type SQL inexprimable en champ.
- **Résoudre le type en lisant la PK de l'entité cible** dans le normaliseur : inutile puisque toutes les PK sont `identity_type()` ; on évite ainsi de donner au normaliseur la connaissance des autres entités.
