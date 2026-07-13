# ADR-083 : Suppression logique (`options.soft_delete`)

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-14

## Contexte

L'option d'entité `options.soft_delete: true` est documentée comme offrant une « suppression logique » : les enregistrements supprimés sont conservés en base avec une date de suppression.

En réalité, elle ne tenait pas ce contrat. Le normaliseur ajoutait une colonne `deleted_at DATETIME NULL`, mais le CRUD généré :

- exposait `deleted_at` comme un champ de saisie ordinaire (formulaire, liste, fiche détail), comme les horodatages avant ADR-081 ;
- effectuait un `DELETE` physique, sans jamais poser `deleted_at` ;
- ne filtrait aucune lecture sur `deleted_at IS NULL`.

L'option promettait une suppression logique et en faisait une suppression physique : un contrat public rompu (charte principe 10, principe 3, refuser la magie cachée). Retour terrain, même famille que F56 (ADR-081).

## Décision

`options.soft_delete: true` produit une **suppression logique réelle**. `deleted_at` est un champ **géré par le framework**, comme les horodatages, avec un comportement de suppression dédié.

### Marqueur

Le normaliseur marque `deleted_at` avec `managed = "soft_delete"` (le marqueur générique d'ADR-081, valeur validée par `ALLOWED_MANAGED_VALUES`).

### Comportement du CRUD généré

- **Exclusion des vues et de l'écriture** : `deleted_at` est absent du formulaire, de la liste, de la fiche détail, de l'export CSV et du tri (comme tout champ `managed`). Il est aussi absent de l'`INSERT` et de l'`UPDATE` : l'application ne le pose jamais.
- **Suppression** : `delete_<entité>` devient `UPDATE <table> SET deleted_at = datetime.now(timezone.utc) WHERE <pk> = ?`, au lieu d'un `DELETE`. La suppression groupée fait de même sur un `IN (...)`.
- **Lectures filtrées** : toutes les lectures du modèle filtrent `deleted_at IS NULL` : `SELECT_ALL`, `SELECT_BY_ID`, `count_*`, `find_*_paginated`, `find_*_for_export` (qui délègue) et le lookup par slug. Un enregistrement supprimé logiquement n'apparaît plus.

### Pas de valeur par défaut SQL

Le DDL reste `deleted_at DATETIME NULL`, sans `DEFAULT`. La valeur est posée par Python à la suppression (cohérent avec ADR-081 : une seule autorité).

## Conséquences

- `options.soft_delete: true` tient enfin son contrat : suppression réversible en base, invisible des lectures.
- Surface : extension du marqueur `managed` (valeur `soft_delete`), additive. Le modèle importe `datetime` dès qu'un champ géré ou une suppression logique pose une valeur temporelle.
- Sans `soft_delete`, la suppression reste physique : non-régression.
- **Limites (version minimale)** : pas de commande de **restauration** ni de vue « corbeille » générées ; l'application les ajoute si besoin. Les listes de choix d'une relation (`many_to_one`) vers une entité soft-deletable ne filtrent pas encore `deleted_at IS NULL` de la cible ; à traiter si le besoin se confirme (règle B, révéler avant d'élargir).

## Alternatives écartées

- **Ne masquer que `deleted_at` des vues (comme les horodatages) sans changer la suppression.**
  Écartée : corrige l'UX mais laisse le contrat « suppression logique » mensonger (le `DELETE` reste physique).
- **Retirer l'option `soft_delete`.**
  Envisagée (un contrat rompu est pire qu'une absence de feature) ; écartée car la suppression logique est un besoin réel et l'implémentation minimale correcte est bornée.
- **Défaut SQL / trigger pour poser `deleted_at`.**
  Écartée : Python reste la seule autorité sur la valeur (cohérent ADR-081), et la portabilité entre backends (ADR-054) est plus simple.

## Référence

- Charte : `CHARTE_DOC.md` (principe 3, refuser la magie cachée ; principe 10, une API publique est un contrat de complétude).
- [ADR-081](081-managed-timestamps.md) : horodatages gérés, marqueur `managed`.
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités.
