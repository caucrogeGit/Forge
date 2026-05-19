# ADR-012 — Politique de dépréciation et suppression du format legacy des entités Forge

## Statut

**Mise à jour — Forge 3.x** (ticket `LEGACY-REMOVE-004-UPDATE-DOCS-AFTER-LEGACY-REMOVAL`).

La décision initiale (dépréciation avec support temporaire) a été remplacée par la suppression
effective du support legacy dans les tickets LEGACY-REMOVE-001A, 001B, 002 et 003.

---

## Date

2026-05-19 (initiale) — mise à jour 2026-05-19

---

## Contexte

Forge a historiquement utilisé un format interne pour les entités, dit **format legacy**,
identifié par la clé `format_version: 1`. Ce format inclut des clés comme `sql_type`,
`python_type`, `primary_key`, `auto_increment`, `from_entity`, `to_entity`, `foreign_key_name`.

Un format canonique a été introduit : `schema_version: "1.0"`, avec des types Forge abstraits
(`string`, `integer`, `boolean`, `date`, `datetime`, `text`, `password`), sans champ `id`
explicite, et `from`/`to`/`foreign_key` pour les relations.

L'audit LEGACY-POLICY-001 (2026-05-19) avait établi que le pipeline dépendait encore du
format legacy. La décision initiale était de déprécier sans supprimer immédiatement.

Les tickets LEGACY-REMOVE-001A et 001B ont ensuite refusé les entités `format_version: 1`
dans `build:model` et `make:crud`. Le ticket LEGACY-REMOVE-002 a refusé le format legacy
dans `relations.json`. Le ticket LEGACY-REMOVE-003 a nettoyé les fixtures de tests restantes.

Aucun projet réel Forge n'était à préserver — la suppression a été faite pendant la phase
de construction du framework.

---

## Décision (mise à jour — remplace la décision initiale)

**Le format canonique `schema_version: "1.0"` est le seul format d'entrée accepté.**

Le format legacy `format_version: 1` est **refusé** :

- `build:model` refuse les entités `format_version: 1` — lève `ModelValidationError`.
- `make:crud` refuse les entités `format_version: 1` — quitte avec `SystemExit`.
- `relations.json` avec `format_version: 1` est refusé par `validate_relations_definition` — lève `EntityRelationsError`.
- Les clés relationnelles legacy (`from_entity`, `to_entity`, `foreign_key_name`, `pivot_table`,
  `source_key`, `target_key`) ne sont pas acceptées dans `relations.json`.

---

## Ancienne décision (archivée)

La décision initiale de l'ADR-012 était :

> Le format legacy `format_version: 1` est déprécié. Il reste accepté temporairement
> pour assurer la compatibilité des projets existants, mais ne doit plus être utilisé dans
> les nouveaux développements.

Cette décision est **remplacée**. Le support temporaire a été supprimé dans les tickets
LEGACY-REMOVE-001A, 001B, 002 et 003.

---

## Ce qui est refusé

| Clé / mécanisme | Statut |
|---|---|
| `format_version: 1` dans les entités | **Refusé** — `build:model`, `make:crud` lèvent une erreur |
| `format_version: 1` dans `relations.json` | **Refusé** — `validate_relations_definition` lève une erreur |
| `from_entity` / `to_entity` dans `relations.json` | **Refusé** |
| `foreign_key_name` dans `relations.json` | **Refusé** |
| `pivot_table` / `source_key` / `target_key` dans `relations.json` | **Refusé** |
| `sql_type` / `python_type` dans les entités | Non accepté par le JSON Schema canonique |
| `primary_key` / `auto_increment` dans les entités | Non accepté par le JSON Schema canonique |

---

## Ce qui reste fonctionnel à bas niveau

`validate_entity_definition()` et `normalize_entity_definition()` sont des fonctions internes
du pipeline. Elles n'ont pas été modifiées et continuent de traiter le format interne legacy
pour les tests de refus. Elles ne constituent pas une API utilisateur.

---

## Règles pour les nouveaux développements

1. **Format obligatoire** : `schema_version: "1.0"` dans tous les fichiers d'entités.
2. **Starters** : format canonique uniquement (migration 100 % réalisée).
3. **Tests** : les fixtures d'entités n'utilisent plus `format_version: 1`, sauf dans les
   tests de refus explicites (tests de régression pour `build:model` et `make:crud`).
4. **Documentation** : aucun exemple ne présente `format_version: 1` comme format utilisable.

---

## Conséquences

- **Projets en `format_version: 1`** : `build:model` et `make:crud` refuseront de traiter
  ces fichiers. Migrer via le guide `docs/entities/migration-legacy-vers-canonique.md`.
- **`relations.json` en `format_version: 1`** : `validate_relations_definition` lèvera
  `EntityRelationsError`. Migrer au format canonique `schema_version: "1.0"`.
- **Starters** : déjà conformes (migration 100 % réalisée dans STARTERS-MIGRATE-001 à 005).

---

## Tickets ayant mis en œuvre cette décision

| Ticket | Résultat |
|---|---|
| `LEGACY-REMOVE-001A` | `build:model` refuse les entités `format_version: 1` |
| `LEGACY-REMOVE-001B` | `make:crud` refuse les entités `format_version: 1` |
| `LEGACY-REMOVE-002` | `relations.json` `format_version: 1` refusé ; clés legacy refusées |
| `LEGACY-REMOVE-003` | Fixtures de tests legacy nettoyées |
| `LEGACY-REMOVE-004` | Documentation alignée sur la suppression du legacy |

---

## Référence

- Guide de conversion : `docs/entities/migration-legacy-vers-canonique.md`
- Audit de plan : `docs/history/audits/legacy-remove-plan-001.md`
- Migrations starters : `STARTERS-MIGRATE-001` à `005`
