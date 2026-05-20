# Limites assumées des contrats JSON

Les contrats JSON Schema renforcent la cohérence de Forge, mais ne prétendent
pas tout vérifier ni tout générer. Cette page récapitule ce que les contrats
garantissent, ce qu'ils ne garantissent pas encore, et ce qui reste
volontairement hors périmètre.

---

## JSON Schema et validation sémantique

Forge distingue deux niveaux de validation :

```text
entity.schema.json  →  validation de structure (JSON Schema)
forge entity:validate  →  validation sémantique complète
```

**JSON Schema vérifie la forme** des fichiers : clés autorisées, types JSON,
valeurs `enum`, propriétés requises. Il ne connaît pas les règles propres à Forge.

**La validation sémantique Forge** va plus loin. Elle vérifie des règles que
le JSON Schema ne peut pas exprimer :

- un index doit pointer vers un champ déclaré dans `fields[]` ;
- une relation doit référencer une entité qui existe dans `mvc/entities/` ;
- deux entités ne peuvent pas partager la même valeur `table` ;
- un pivot `many_to_many` ne peut pas être déclaré deux fois en inverse ;
- `pivot.fields[]` ne peut pas redéclarer `id`, `from_key` ou `to_key`.

Ces règles sémantiques ne sont détectées que par `forge entity:validate`,
pas par un éditeur ou un validateur JSON Schema seul.

---

## VS Code aide, mais ne valide pas tout

VS Code peut proposer des clés, des valeurs `enum` et signaler des erreurs de
structure à partir des schémas Forge. Ce n'est pas une validation officielle.

**Exemples de cas que VS Code ne peut pas détecter :**

- une relation pointant vers une entité inexistante dans le projet ;
- deux entités déclarant la même table SQL ;
- une relation `many_to_many` inverse dupliquée ;
- un index référençant un champ absent de `fields[]` ;
- la cohérence complète avec les générateurs (`build:model`, `make:crud`).

La commande officielle de diagnostic reste :

```bash
python forge.py entity:validate
```

Voir [Autocomplétion VS Code](vscode-json-schema.md) pour la configuration
détaillée de l'aide à la saisie.

---

## Format legacy refusé

Le format `format_version: 1` n'est plus accepté comme format d'entrée utilisateur.

- `build:model` refuse les entités `format_version: 1` — lève `ModelValidationError`.
- `make:crud` refuse les entités `format_version: 1` — quitte avec `SystemExit`.
- `relations.json` avec `format_version: 1` est refusé par `validate_relations_definition`.
- Les clés legacy (`from_entity`, `to_entity`, `foreign_key_name`) sont refusées.

**Migration** : voir `docs/entities/migration-legacy-vers-canonique.md`.

Les starters distribués avec Forge sont tous au format canonique `schema_version: "1.0"`.
La suppression du support legacy a été réalisée dans les tickets LEGACY-REMOVE-001A, 001B,
002 et 003, pendant la phase de construction du framework (aucun projet réel à préserver).

---

## Attributs pivot et CRUD avancé

`pivot.fields[]` est validé par `entity:validate` et projeté en SQL par
`build:model`. Les champs pivot peuvent exister dans le contrat et être générés
en base.

**Garde-fou `make:crud` :** si un champ pivot est `required: true` ou
`nullable: false`, `make:crud` refuse de générer le CRUD et affiche un message
d'erreur. En effet, `make:crud` synchronise uniquement les identifiants — un
champ `NOT NULL` sans valeur fournie produirait une erreur d'intégrité à
l'exécution. Pour lever ce blocage, rendez les champs pivot nullable ou utilisez
un module CRUD pivot dédié.

**Ce qui reste hors périmètre actuel :**

- l'édition des attributs pivot dans les formulaires CRUD générés par `make:crud` ;
- l'affichage des attributs pivot dans les vues `list` et `show` générées.

Le CRUD avancé pour les attributs `pivot.fields[]` n'est pas encore couvert
comme fonctionnalité complète. C'est une limite assumée, pas un oubli.

---

## Mapping SQL : limites actuelles

Le mapping des types Forge vers MariaDB est documenté dans
[Types Forge vers MariaDB](types-forge-mariadb.md). Certaines limites sont
assumées :

| Propriété | Comportement actuel |
|-----------|---------------------|
| `min` / `max` | conservés dans la structure interne, **ne génèrent pas de contrainte SQL `CHECK`** |
| `default` | projeté en SQL `DEFAULT` pour les cas courants |
| `nullable` | la règle est définie par ADR-013 : `nullable` par défaut (`NULL`), `required: true` prioritaire (`NOT NULL`) — uniforme pour `fields[]` et `pivot.fields[]` |
| `boolean` | projeté en `BOOLEAN` MariaDB |

Le SQL généré est une **projection Forge**, pas un dialecte configurable par
l'application. L'utilisateur ne peut pas personnaliser le dialecte SQL.

---

## entity:validate ne vérifie pas la base réelle

`forge entity:validate` vérifie les contrats JSON canoniques. Elle ne compare
pas le contrat courant avec l'état réel d'une base MariaDB déjà déployée.

**Exemples de ce que `entity:validate` ne détecte pas :**

- une colonne présente en base mais absente du contrat ;
- une colonne absente de la base mais déclarée dans le contrat ;
- un index présent en base mais supprimé du contrat ;
- un type SQL divergeant entre la base et le contrat.

Pour comparer l'état réel de la base avec le contrat courant, utiliser les
commandes de migration ou les outils MariaDB adaptés.

---

## Générateurs protégés, mais pas magiques

`build:model`, `make:crud` et les migrations protégées utilisent les contrats
JSON comme garde-fous : ils refusent de générer si `entity:validate` détecte
des erreurs.

**Ce qu'ils ne font pas :**

- corriger automatiquement un contrat invalide ;
- migrer automatiquement un ancien starter vers le format canonique ;
- garantir toute la logique applicative (contrôleurs, vues, règles métier) ;
- détecter les divergences entre la base déployée et le contrat courant.

Les générateurs sont **explicites par conception** : ils génèrent ce que le
contrat déclare, sans inférence cachée.

---

## Travaux futurs possibles

Ces points ne sont pas des engagements — ce sont des pistes identifiées pendant
la phase bêta :

- harmonisation du comportement `nullable` entre `fields[]` et `pivot.fields[]` ;
- support CRUD avancé des attributs `pivot.fields[]` dans `make:crud` ;
- configuration VS Code prête à l'emploi (`.vscode/settings.json` dans les starters) ;
- vérification plus poussée entre contrat et état réel d'une base MariaDB ;
- support éventuel de `one_to_one`, relations polymorphiques ou clés primaires personnalisées.

Chacun de ces points fera l'objet d'un ticket séparé s'il est décidé.
