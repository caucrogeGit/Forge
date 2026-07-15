# ADR-086 : Élimination de la représentation legacy interne du moteur d'entités

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.
Prolonge l'ADR-012 (dépréciation du format legacy) et l'ADR-070 (extraction du moteur d'entités).

## Date

2026-07-15

## Contexte

Le format d'entrée des entités est le format canonique `schema_version: "1.0"`
(types Forge abstraits : `string`, `integer`, `datetime`...).
L'ADR-012 a supprimé le support du format legacy `format_version: 1` en entrée :
`build:model` et `make:crud` le refusent.

Il subsiste pourtant une représentation legacy à l'intérieur du pipeline.
Le fichier canonique est ponté vers un dict dit « legacy interne » par
`normalize_canonical_entity_for_model_build()` (canonical_model_normalizer.py),
puis validé et normalisé par `validate_entity_definition()` /
`normalize_entity_definition()` (validation.py, 873 lignes), avant d'être passé
aux générateurs `build_entity_sql()` / `build_entity_base()`.
Ce dict porte des clés dérivées absentes du canonique : par champ `sql_type`,
`python_type`, `column`, `primary_key`, `auto_increment`.

Six sous-systèmes lisent ce dict interne : générateurs SQL/modèle, CRUD,
relations, migrations, pages publiques, documentation d'entité.
Le mapping type Forge vers `sql_type`/`python_type`/`column` n'existe qu'à un
seul endroit, enfoui dans le pont ; la validation de cohérence est rédigée en
termes de `sql_type`/`python_type`.

Cette double représentation est une machinerie interne, invisible de
l'utilisateur, mais elle contredit le principe 11 (une seule façon officielle)
et le principe 3 (refuser la magie cachée).
L'ADR-012 note lui-même que `validate_entity_definition()` et
`normalize_entity_definition()` « ne constituent pas une API utilisateur » :
la représentation legacy interne est un artefact de transition, pas un contrat.

L'audit de blast radius (2026-07-15) a établi que le dict interne n'est pas
intrinsèquement nécessaire : rien dans la génération n'exige un pivot
matérialisé.
Tout ce qu'il porte (types résolus, colonnes, PK et horodatages synthétiques)
peut être calculé à la demande depuis le canonique et le dialecte du backend.

## Décision

Éliminer la représentation legacy interne : le pipeline lira le format canonique
directement, sans matérialiser de dict pivot.
La suppression est un refactor purement interne, sans changement de contrat
externe (le format d'entrée reste le canonique) et sans bénéfice visible pour
l'utilisateur ; le gain est une représentation unique et moins de machinerie
cachée.

Le refactor procède par une épopée de tickets, incrémentale, chaque ticket
gardant la suite verte, sans big-bang :

1. **ENTITY-RESOLVER-001** (additif) : extraire le mapping type canonique vers
   `(sql_type, python_type, column)` dans un service partagé `field_resolver`.
   Le pont `canonical_model_normalizer` en devient un mince appelant.
   Aucun changement de comportement.
2. **ENTITY-CANONICAL-ACCESSORS-002** (additif) : exposer un accès canonique aux
   champs (clé primaire, type SQL, type Python, colonne) adossé au service, que
   les générateurs consomment à la place des clés du dict interne.
3. à 8. Migrer les sous-systèmes du plus petit au plus grand, un ticket chacun :
   documentation (`entity_doc`), pages publiques (`public_list`/`public_form`),
   migrations, relations, CRUD (`make_crud` et `crud/*`), SQL/modèle
   (`make_entity`, `model`).
4. **ENTITY-LEGACY-PURGE-FINAL** : plus aucun consommateur ne lit le dict
   interne. Supprimer `normalize_canonical_entity_for_model_build()` et
   l'essentiel de `validation.py` (conserver `to_snake`, `EntityDefinitionError`
   et la validation exprimée en canonique). Retirer les tests de refus devenus
   caducs.

Le levier de réduction du blast radius est que trois primitives concentrent la
logique dérivée (`column_for_field`, déjà canonique ; le mapping vers
`python_type` ; le mapping vers `sql_type`, dialectal).
Les exposer comme service, puis comme accesseurs, convertit la majorité des
`field["sql_type"]`/`field["column"]`/`field["python_type"]` en appels de
service, sous-système par sous-système.

## Conséquences

- Aucun changement de format d'entrée ni d'API publique du moteur d'entités.
  `column_for_field` et `CanonicalNormalizationError` restent importables depuis
  `canonical_model_normalizer` par ré-export ; les fixtures (ADR-077) ne sont
  pas touchées.
- Le service `field_resolver` devient la source unique du mapping type vers SQL
  et Python (principe 11). Il ne dépend que du contrat `Dialect` (ADR-054),
  jamais d'un backend concret.
- L'épopée est multi-sessions ; chaque ticket est indépendamment livrable et
  vérifiable. La suite de tests d'entités sert de filet de non-régression à
  chaque étape.
- Le ticket final retire une grande partie de `validation.py` : la validation de
  cohérence rédigée en `sql_type`/`python_type` est remplacée par une validation
  canonique, en partie déjà assurée en amont par les schémas JSON (`cli/schemas`).

## Limites

- Cet ADR ne change ni le format canonique des entités, ni le format de
  `relations.json`, ni le contrat des schémas JSON canoniques.
- La synthèse des champs système (clé primaire `id`, horodatages, soft delete)
  reste une étape de génération ; son extraction éventuelle vers un énumérateur
  de champs canoniques relève des tickets de migration des sous-systèmes, pas de
  cet ADR.
- Il ne préjuge pas de la prise en charge des `indexes[]` canoniques, aujourd'hui
  ignorés par `build:model` : ce serait un ticket distinct.
