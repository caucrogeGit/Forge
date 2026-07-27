# Audit : branchement des générateurs sur des noms de types SQL

**Ticket** : `OPTIN-SQL-TYPE-BRANCHING-AUDIT-001`
**Date** : 2026-07-27
**Auteur** : Forge (audit pré-implémentation, mesure sur les quatre dialectes)
**Périmètre** : le code qui **décide d'un comportement** à partir d'un nom de type SQL

---

## 1. Résumé

Le chantier `OPTIN-DDL-DIALECTAL` a rendu portable l'**émission** de DDL.
Cet audit porte sur un défaut voisin mais distinct, découvert en élargissant le scan du garde-fou : du code qui **lit** un nom de type SQL pour en déduire une décision.

Ce défaut est plus sournois que le précédent.
Un DDL non portable échoue franchement, avec une erreur de syntaxe claire.
Un branchement sur un nom de type ne produit **aucune erreur** : la condition est simplement fausse, la branche ne s'exécute pas, et la fonctionnalité disparaît en silence.

Mesuré sur les quatre dialectes, l'effet le plus grave concerne **SQL Server** : ses types commencent par `NVARCHAR`, qui ne correspond à aucun préfixe attendu.

| Fonctionnalité | MariaDB | SQLite | PostgreSQL | SQL Server |
|---|---|---|---|---|
| Recherche `LIKE` du CRUD généré | oui | oui | oui | **aucune colonne** |
| Rendu `textarea` d'un champ texte | oui | oui | oui | **non** |
| Libellés de relation (mêmes champs) | oui | oui | oui | **aucun** |
| Filtres de liste `VARCHAR` | oui | **non** | oui | **non** |
| Champ de formulaire texte accepté | oui | oui | oui | **non** |

Aucun correctif n'est appliqué dans ce ticket.

---

## 2. Méthode

Les cinq listes de préfixes ont été confrontées à ce que chaque dialecte produit réellement pour un champ Forge `string`, `text`, `datetime` et `float`, en interrogeant les dialectes eux-mêmes.
L'effet de bout en bout a ensuite été vérifié sur une entité à deux champs, un `string` et un `text`, en appelant les fonctions de génération pour chaque backend.

---

## 3. Résultat mesuré, de bout en bout

Pour une entité `Article` portant `titre` (`string`) et `corps` (`text`) :

```
--- mariadb ---
   colonnes de recherche LIKE : ['titre', 'corps']
   champs rendus en textarea  : ['corps']

--- mssql ---
   colonnes de recherche LIKE : AUCUNE
   champs rendus en textarea  : AUCUN
```

Sur SQL Server, le CRUD généré perd donc sa recherche et rend un champ de texte long comme une simple ligne de saisie.
Rien ne le signale, ni à la génération ni à l'exécution.

---

## 4. Emplacements

| Fichier | Ce qui est décidé | Effet hors MariaDB |
|---|---|---|
| `entities/crud/utils.py` (`_is_textarea`) | rendre un `textarea` | SQL Server : jamais |
| `entities/crud/utils.py` (`_text_search_fields`) | colonnes de la recherche `LIKE` et libellés de relation | SQL Server : aucune |
| `entities/validation.py` (`_TEXT_FORM_FIELD_SQL_PREFIXES`) | accepter un champ de formulaire texte | SQL Server : refusé |
| `entities/validation.py` (`_LIST_FILTER_SUPPORTED_SQL_PREFIXES`) | autoriser un filtre de liste | SQLite et SQL Server : refusé |
| `entities/make_crud.py` | valeur de repli `"BIGINT UNSIGNED"` pour une FK | type MariaDB posé sur un autre backend |

`iot/cli/doctor.py` apparaissait au scan mais est **hors sujet** : ses occurrences sont dans une docstring qui documente le correctif de `OPTIN-DDL-IOT-DOCTOR-001`, pas dans du code de décision.

---

## 5. Cause commune

Le code raisonne sur un **nom de type SQL**, qui appartient au dialecte, alors qu'il cherche à connaître une **nature de donnée**, qui appartient au modèle.

Or le contrat `Dialect` expose déjà exactement cette information : `sql_families(sql_type)` rend la famille Python d'un type (`str`, `int`, `datetime`, `float`, `bool`).
Elle a été employée avec succès dans `OPTIN-DDL-IOT-DOCTOR-001`, précisément pour comparer des schémas entre moteurs.

Comme pour le chantier précédent, **rien ne manque au contrat** : ces fonctions ne l'appellent pas.

Le champ canonique porte par ailleurs son type Forge (`text`, `string`) et son `python_type`, disponibles avant toute résolution dialectale : plusieurs de ces décisions pourraient se prendre encore plus en amont, sans consulter le SQL du tout.

---

## 6. Recommandation

Deux niveaux, à trancher par le mainteneur.

**Niveau 1, le minimum.** Remplacer les tests de préfixes par `Dialect.sql_families()`.
Correction locale, sans changement de contrat, qui rétablit le comportement sur les quatre backends.

**Niveau 2, la cause.** Décider à partir du **type Forge** du champ (`text`, `string`, `email`…) plutôt que de son type SQL rendu.
Un `textarea` se déduit de `type: text`, pas de `LONGTEXT` : le générateur n'a aucune raison de redescendre au SQL pour cette décision.
Plus propre et plus stable, mais touche davantage de code et demande de vérifier que le type Forge est disponible partout où ces fonctions sont appelées.

Le cas de `make_crud.py` est distinct et simple : la valeur de repli `"BIGINT UNSIGNED"` doit devenir `dialect.identity_storage_type()`, exactement le correctif de `FK-IDENTITY-STORAGE-TYPE-001`.

Quelle que soit la voie retenue, un garde-fou doit figer le résultat.
Le garde-fou existant, `tests/meta/test_optin_ddl_portability_ratchet_001.py`, couvre l'émission de DDL et n'a plus aucune entrée ; celui-ci demande un contrôle différent, portant sur le **comportement** des générateurs sous chaque backend et non sur le texte des sources.

---

## 7. Reproduire la mesure

Les quatre dialectes suffisent, aucun serveur n'est nécessaire : le défaut est visible dès la génération.
Les quatre moteurs restent disponibles sur la station de développement pour vérifier un correctif de bout en bout.
