# ADR-058 : Source unique des schémas JSON Forge

## Statut

Proposé, Forge 1.0.0-rc (ticket `ADR-SCHEMAS-SINGLE-SOURCE-001`).
Décision d'hygiène et de source de vérité ; relève du mainteneur.

---

## Date

2026-06-29

---

## Contexte

Les schémas JSON du cœur (`common`, `field`, `entity`, `relations`) existaient en
trois copies maintenues à la main, plus l'index `forge.schema.index.json` :

- `cli/schemas/` : source **canonique**. Chargée au runtime par les validateurs
  (`Path(__file__).parent.parent / "schemas"`), exposée par `schema:list` /
  `schema:doctor`, et **packagée** (`MANIFEST.in : recursive-include cli/schemas`).
- `schemas/` (racine du dépôt) : copie « dogfooding », maintenue **identique** à
  `cli/schemas/` par un test de synchro.
- `skeleton/data/schemas/` : gabarit copié dans chaque projet généré par
  `forge new` (`shutil.copyfile`).

Cette duplication est volontaire mais coûteuse : chaque modification de contrat
doit être recopiée à l'identique dans plusieurs dossiers, et un test verrouille
la synchro. Les extractions RBAC (ADR-056) et pivot (ADR-057) ont par ailleurs
introduit des copies de schémas de base (`field`, `common`) dans `forge-mvc-pivot`
pour l'autonomie, augmentant encore le nombre de copies.

Constat vérifié :

- **aucun code du cœur ne lit le `schemas/` racine** : les validateurs lisent
  `cli/schemas/` ; les seules occurrences sont des `$id` (URL) et des libellés de
  conseil destinés au dossier `schemas/` du **projet** utilisateur ;
- depuis l'ADR-044 (dépôt « framework only », application relocalisée), le dépôt
  n'a plus d'entités propres à valider : le `schemas/` racine n'est plus utilisé
  que par la **suite de tests** ;
- `forge new` sème les schémas depuis le **squelette**, pas depuis la racine.

Le `schemas/` racine est donc une **redondance pure**.

---

## Décision

### Une seule source canonique : `cli/schemas/`

`cli/schemas/` est la source de vérité unique des schémas du cœur (elle est déjà
celle qui est chargée et packagée).

### Suppression de la copie racine

Le dossier `schemas/` à la racine du dépôt est **supprimé**.
La suite de tests pointe désormais vers `cli/schemas/`.
Le test de synchro racine vers cli disparaît (plus de copie racine).

### Le squelette reste un gabarit dérivé et gardé

`skeleton/data/schemas/` n'est **pas** une redondance : c'est le gabarit
semé dans les projets générés (les schémas **du projet**, pour la validation IDE
locale).
Il reste, mais comme **artefact dérivé** : un test garde sa synchronisation avec
le canonique `cli/schemas/`.

### Les copies embarquées par les opt-ins sont dérivées et gardées

Les schémas de base copiés dans un opt-in pour son autonomie (par exemple
`field` et `common` dans `forge-mvc-pivot`, ADR-057) restent, mais une garde
vérifie qu'ils restent **identiques** au canonique `cli/schemas/` (anti-dérive).

### Règle

Il y a **un seul canonique** (`cli/schemas/`).
Toute autre présence d'un schéma (squelette, opt-in) est une **copie dérivée**,
explicitement synchronisée et gardée par un test.
Aucune copie « source » parallèle au canonique.

---

## Conséquences

Le dépôt perd un dossier redondant ; une modification de contrat ne se fait plus
qu'à un seul endroit canonique, les copies dérivées étant gardées.
La distinction « source » vs « packagée » disparaît : `cli/schemas/` est les deux.

Blast radius de l'implémentation (ticket distinct) : supprimer `schemas/`
(racine) ; repointer les tests de contrat (`test_entity_json_schema`,
`test_field_json_schema`, `test_common_json_schema`, `test_relations_json_schema`,
`test_forge_schema_index`) vers `cli/schemas/` ; réécrire le garde de synchro
(retrait racine vers cli ; conservation skeleton vers cli ; ajout opt-in base
vers cli) ; mettre à jour la documentation qui décrivait la copie racine.

---

## Alternatives écartées

**Garder `schemas/` racine comme source « dogfooding ».**
Plus d'application au dépôt depuis l'ADR-044 : la copie racine ne sert qu'aux
tests, c'est une redondance.

**Faire du `schemas/` racine la source et générer `cli/schemas/`.**
Inverse le canonique : or `cli/schemas/` est la copie chargée au runtime et
packagée. Le canonique naturel est `cli/schemas/`.

**Semer le squelette directement depuis `cli/schemas/` au lieu d'un gabarit
stocké.**
Possible, mais c'est une évolution de `forge new` hors périmètre de cette
décision d'hygiène. Le gabarit stocké reste, gardé en synchro.

---

## Charte appliquée

- Principe 11 (une seule façon officielle) : un seul canonique de schémas.
- Principe 3 (refus de la magie cachée) : les copies dérivées sont explicites et
  gardées par des tests.
- Règle A (retirer la cause) : on supprime la copie redondante plutôt que de
  maintenir une synchro inutile.

---

## Référence

- [ADR-044](044-framework-only-repo.md) : dépôt framework only (application relocalisée).
- [ADR-056](056-rbac-contract-tooling-extraction.md) : extraction du schéma RBAC.
- [ADR-057](057-pivot-schema-decoupling.md) : découplage et extraction du schéma pivot.
- `cli/schemas/` : source canonique ; `MANIFEST.in` la package.
