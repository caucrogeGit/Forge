# ADR-079 : Découpeur d'instructions SQL canonique dans le cœur

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-13

## Contexte

Plusieurs commandes Forge exécutent un script SQL multi-instructions et doivent le découper en instructions individuelles sur les `;` : `migration:apply` et `db:apply` (`forge-mvc-entities`), `fixtures:load` (`forge-mvc-fixtures`).

Deux découpeurs distincts coexistaient, chacun incomplet :

- `forge_mvc_entities.db_apply.split_sql_statements` : conscient des chaînes `'...'` (correctif du retour terrain 012, apostrophe), mais **pas des commentaires** ;
- `forge_mvc_fixtures.cli.load.split_sql_statements` : conscient des chaînes `'...'` et de l'échappement `''`, précédé d'un retrait des **lignes** de commentaire `--`, mais aveugle aux commentaires `--` en fin de ligne et aux blocs `/* */`.

Le retour terrain 021 a exposé la conséquence : une migration dont un **commentaire** contient un `;` casse (`You have an error in your SQL syntax ... near '<texte après le ;>'`), le `;` du commentaire étant pris pour un séparateur.

C'est la même famille de bug que le retour 012 (split cassé par une apostrophe). À fiabiliser une bonne fois, avec une seule implémentation robuste.

## Décision

Le cœur expose un découpeur **canonique** unique, `core.database.sql_script.split_sql_statements(sql)`, conscient à la fois des **littéraux** et des **commentaires** :

- chaînes `'...'` avec échappement `''` : un `;` à l'intérieur n'est pas un séparateur ;
- commentaires de ligne `-- ... <fin de ligne>` et de bloc `/* ... */` : un `;` à l'intérieur n'est pas un séparateur ; les commentaires sont **retirés** des instructions produites (remplacés par une espace pour ne pas coller deux tokens) ;
- les instructions vides (ou uniquement commentaire/espace) sont ignorées.

`forge-mvc-entities` (`migration:apply`, `db:apply`) et `forge-mvc-fixtures` (`fixtures:load`) consomment ce découpeur ; leurs implémentations locales sont **supprimées** (principe 11, une seule façon officielle). Les deux paquets dépendent déjà du cœur.

Le découpage sert le chemin d'**exécution** ; l'affichage relu (`fixtures:load` en mode par défaut, charte §7) montre toujours le fichier `.sql` intact, commentaires compris.

## Conséquences

- Un `;` dans un commentaire ou une chaîne ne casse plus ni `migration:apply`, ni `db:apply`, ni `fixtures:load` : le bug est corrigé au même endroit pour toutes les commandes.
- Le cœur gagne un petit utilitaire pur (sans dépendance) dans son périmètre d'accès BDD minimal (ADR-004) ; les opt-ins n'ont plus à réimplémenter le découpage.
- `forge-mvc-fixtures` réexporte `split_sql_statements` depuis `forge_mvc_fixtures.cli.load` (compatibilité de son API de module) ; il délègue au cœur.

## Alternatives écartées

- **Corriger seulement `db:apply`.**
  Écartée : laisserait deux découpeurs divergents et le même bruit reviendrait ailleurs (principe 11).
- **Une bibliothèque de parsing SQL tierce.**
  Hors charte : dépendance lourde pour un besoin borné ; le runtime Forge reste volontairement limité.
- **Retrait des commentaires par expression régulière avant le split.**
  Fragile : une regex ne distingue pas un `--` dans une chaîne d'un vrai commentaire ; l'automate à états le fait correctement.

## Référence

- Charte : `CHARTE_DOC.md` (principe 11, une seule façon officielle ; règle A, retirer la cause).
- [ADR-004](004-core-perimeter.md) : périmètre du cœur minimal (accès BDD).
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités (`migration:apply`, `db:apply`).
- [ADR-074](074-fixtures-optin.md) : opt-in fixtures (`fixtures:load`).
