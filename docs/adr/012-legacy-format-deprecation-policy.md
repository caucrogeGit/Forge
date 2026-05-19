# ADR-012 — Politique de dépréciation du format legacy des entités Forge

## Statut

Acceptée — Forge 3.x (ticket `LEGACY-POLICY-002-DOCUMENT-LEGACY-DEPRECATION-POLICY`).

---

## Date

2026-05-19

---

## Contexte

Forge a historiquement utilisé un format interne pour les entités, dit **format legacy**,
identifié par la clé `format_version: 1`. Ce format inclut des clés comme `sql_type`,
`python_type`, `primary_key`, `auto_increment`, `from_entity`, `to_entity`, `foreign_key_name`.

Un format canonique a été introduit progressivement : `schema_version: "1.0"`, avec des
types Forge abstraits (`string`, `integer`, `boolean`, `date`, `datetime`, `text`, `password`),
sans clé `id` dans les champs, et `from`/`to`/`foreign_key` pour les relations.

L'audit LEGACY-POLICY-001 (2026-05-19) a établi les faits suivants :

- Le format legacy est encore profondément présent dans le pipeline de génération
  (`build:model`, `make:crud`, `make:entity`, migrations) via le normaliseur interne
  (`canonical_model_normalizer.py`).
- 55 fichiers de tests utilisent `format_version: 1` (187+ occurrences).
- Tous les starters distribués sont migrés en format canonique (migration complète 100 %).
- Deux anomalies ont été corrigées dans la foulée :
  `LEGACY-STARTERRELS-FIX-001` (drop_foreign_keys) et
  `LEGACY-SCAFFOLD-FIX-001` (détection relations vides canoniques).

La suppression immédiate du support legacy casserait le pipeline interne et 55 fichiers
de tests. Elle est hors scope.

---

## Décision

**Le format canonique `schema_version: "1.0"` est le format officiel et recommandé de Forge.**

Le format legacy `format_version: 1` est **déprécié**. Il reste accepté temporairement
pour assurer la compatibilité des projets existants, mais ne doit plus être utilisé dans
les nouveaux développements.

---

## Ce qui est déprécié

| Clé / mécanisme | Statut |
|---|---|
| `format_version: 1` (identifiant du format) | Déprécié |
| `sql_type` (type SQL explicite dans le JSON) | Déprécié |
| `python_type` (type Python explicite dans le JSON) | Déprécié |
| `primary_key` (déclaration explicite de la PK) | Déprécié |
| `auto_increment` (auto-incrément explicite) | Déprécié |
| `from_entity` / `to_entity` (clés de relation legacy) | Déprécié |
| `foreign_key_name` (nom de contrainte FK legacy) | Déprécié |
| Recommander le legacy dans les exemples ou la doc | Interdit |
| Créer de nouveaux starters en format legacy | Interdit |

---

## Ce qui reste supporté temporairement

| Mécanisme | Raison du maintien |
|---|---|
| `validate_entity_definition()` / `normalize_entity_definition()` | Format interne du pipeline de génération |
| `canonical_model_normalizer.py` — pont canonique → legacy | Nécessaire pour `build:model`, `make:crud` |
| Lecture des entités legacy dans `build:model`, `make:crud`, `make:relation` | Compatibilité projets existants |
| Fixtures de tests legacy (55 fichiers, 187+ occurrences) | Réécriture non planifiée dans ce ticket |

Le support temporaire **ne constitue pas une garantie de stabilité à long terme**.

---

## Ce qui n'est pas encore supprimé

- `format_version: 1` dans les fichiers d'entités existants des projets utilisateurs.
- Les fonctions internes `validate_entity_definition()`, `normalize_entity_definition()`.
- Les tests qui utilisent le format legacy comme fixture d'entrée.
- Les fichiers de tests qui testent explicitement le comportement legacy.

---

## Règles pour les nouveaux développements

1. **Nouveaux starters** : format canonique obligatoire (`schema_version: "1.0"`).
2. **Nouveaux exemples dans la documentation** : format canonique uniquement.
3. **Nouveaux fichiers d'entités** : `make:entity` produit déjà le format canonique.
4. **Nouveaux tests** : utiliser le format canonique comme fixture par défaut.
   Le format legacy n'est acceptable que pour tester explicitement la compatibilité legacy.
5. **Avertissements runtime** : non introduits dans ce ticket. Voir ticket futur
   `LEGACY-WARNINGS-001` si la politique de dépréciation active est décidée.

---

## Conditions avant suppression future

La suppression du format legacy ne pourra être envisagée que lorsque **toutes** les
conditions suivantes seront remplies :

1. Les 55 fichiers de tests legacy sont reclassés : migrés en canonique ou explicitement
   étiquetés comme « tests de compatibilité legacy » à supprimer avec le support.
2. Un guide de migration pour les projets existants en `format_version: 1` existe.
3. Les commandes produisent un message d'erreur ou d'avertissement explicite si une entité
   legacy est refusée (pas de comportement silencieux).
4. Le format interne du pipeline de génération (`build:model`, `make:crud`) a été migré
   pour ne plus dépendre de `format_version: 1` comme représentation intermédiaire.
5. Une version cible de suppression a été décidée et documentée dans un ticket dédié.
6. Aucun starter distribué ne dépend du format legacy (déjà acquis — 100 % canonique).

La suppression sera traitée dans le ticket `LEGACY-REMOVE-001`, dans une version majeure future.

---

## Conséquences

- **Court terme** : aucun changement de comportement. Le legacy est toléré silencieusement.
- **Moyen terme** : si `LEGACY-WARNINGS-001` est implémenté, les commandes avertiront
  lors de l'utilisation d'entités legacy.
- **Long terme** : `LEGACY-REMOVE-001` supprimera le support dans une version majeure.
- **Documentation** : la doc existante (`docs/entities/entity-schema.md`) signale déjà
  les clés legacy comme interdites dans les fichiers canoniques. Cette ADR formalise
  la politique au niveau du framework.
- **Starters** : déjà conformes (migration 100 % réalisée dans STARTERS-MIGRATE-001 à 005).

---

## Tickets futurs possibles

| Ticket | Objectif |
|---|---|
| `LEGACY-WARNINGS-001` | Ajouter des warnings runtime pour les entités legacy |
| `LEGACY-TESTS-RECLASSIFY-001` | Reclasser les 55 fichiers de tests legacy |
| `LEGACY-MIGRATION-001` | Guide de migration pour projets en `format_version: 1` |
| `LEGACY-REMOVE-001` | Supprimer le support legacy (version majeure future) |

---

## Référence

- Audit : `docs/history/audits/legacy-support-core-audit-001.md`
- Migrations starters : `STARTERS-MIGRATE-001` à `005`
- Correctifs legacy : `LEGACY-STARTERRELS-FIX-001`, `LEGACY-SCAFFOLD-FIX-001`
