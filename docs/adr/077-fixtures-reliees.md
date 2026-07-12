# ADR-077 : Fixtures reliées (colonnes réelles, références inter-fixtures, ordre par dépendances)

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-12

## Contexte

L'opt-in `forge-mvc-fixtures` (ADR-074, ADR-076) charge, purge et génère des jeux de données.
Un projet banc d'essai (RéférenCiel Manager) a voulu remplacer son seed de démo maison par des fixtures natives, et trois manques l'en ont empêché.

Sur une entité `eleve` (contrat en snake_case, colonnes SQL en PascalCase), `fixtures:make-factory` puis `fixtures:generate` produisent :

```sql
INSERT INTO eleve (nom, prenom, identifiant, date_naissance, user_id)
VALUES ('Lucas', 'Hélène', 'beau', '1984-06-02', 507);
```

Trois défauts :

1. les colonnes sont les **noms de champs** du contrat (`nom`, `user_id`), pas les colonnes réelles de la table (`Nom`, `UserId`) ;
2. `user_id = 507` est un `random_int` : aucune fixture ne peut référencer l'`Id` d'une ligne créée par une autre ;
3. `fixtures:load` charge les fichiers dans l'ordre du nom, sans respecter les dépendances de clés étrangères, donc les FK cassent.

Impossible d'obtenir un jeu de données cohérent et relié. Les correctifs doivent être **généraux** et vivre dans le paquet, pas dans l'application.

Rappel du mapping (normaliseur `forge-mvc-entities`, ADR-069) : la PK est `Id` ; un champ `foreign_key` garde son nom snake (`annee_scolaire_id`) ; un champ ordinaire passe en PascalCase (`user_id` vers `UserId`). Les clés étrangères sont déclarées dans `mvc/entities/relations.json`.

## Décision

### F45 : colonnes réelles

`fixtures:make-factory` échafaude le dict de la factory avec les **colonnes réelles** de l'entité, plus les noms de champs.

Le mapping champ vers colonne est la convention canonique du normaliseur : `Id` pour la PK, nom snake conservé pour un `foreign_key`, PascalCase sinon.
`forge-mvc-fixtures` l'obtient via `forge-mvc-entities`, producteur des contrats : ce dernier expose une fonction publique `column_for_field(field)` que fixtures importe (dépendance **douce** : si `forge-mvc-entities` est absent, repli sur le nom de champ, mode dégradé documenté).

`fixtures:generate` est **inchangé** : il rend les clés du dict telles quelles. Les factories portant désormais les colonnes réelles, le SQL généré utilise `Nom`, `UserId`, etc., correct pour le backend installé (cohérent ADR-075).

### F43 : références inter-fixtures

Nouvelle API de `Factory` : `self.reference(table, key_column, value)` renvoie un sentinelle `FixtureReference` au lieu d'une valeur littérale.

`fixtures:generate` détecte ce sentinelle et rend, à la place d'un littéral, une **sous-requête SQL** :

```sql
(SELECT Id FROM users WHERE Email = 'prof.durand@ecole.fr' LIMIT 1)
```

La résolution se fait donc à la **charge** (`fixtures:load`), contre les vrais `Id` auto-incrémentés : robuste, et le SQL reste **visible et relu** (principe 5). La valeur de recherche est rendue par `dialect.render_literal` ; la PK cible est `Id` (convention du normaliseur).

`fixtures:make-factory` : pour un champ **clé étrangère** (type `foreign_key`, ou FK de l'entité déclarée dans `relations.json`), échafaude un `self.reference("<table cible>", "<clé naturelle>", ...)` commenté (avec un TODO sur la clé naturelle) au lieu de `random_int`.

### F44 : ordre de chargement par dépendances FK

`fixtures:load` ordonne les fichiers par **tri topologique** du graphe de dépendances déduit de `relations.json` : une entité est chargée après celles qu'elle référence (les `users` avant `eleve`, `annee_scolaire`/`niveau_classe` avant `classe`).
Chaque fichier `.sql` est rattaché à sa table (via `INSERT INTO <table>`), puis à son entité.

Replis :

- `relations.json` absent, table inconnue, ou **cycle** de dépendances : retour à l'ordre par nom de fichier (le préfixe numérique `01_`, `02_` reste un ordre déclaratif de secours) ;
- option `--no-fk-checks` : encadre le chargement par la désactivation des contraintes du dialecte (`SET FOREIGN_KEY_CHECKS=0/1` en MariaDB ; équivalent PostgreSQL exposé par le backend), pour les jeux non triables.

### Piste « fixtures callable » (différée)

Deux étapes d'un seed complet restent de la logique métier hors SQL : import d'un référentiel depuis un JSON canonique, et données calculées (agrégations).
Un hook Python exécuté par `fixtures:load` sort du modèle « SQL visible, relu » et mérite un examen séparé (dépendance, ordre, sécurité).
**Différé**, hors de cet ADR.

## Mise en œuvre (phasage)

Tickets distincts, dans cet ordre :

1. **F45** : `column_for_field` public dans `forge-mvc-entities` ; `make-factory` scaffolde les colonnes réelles.
2. **F43** : `Factory.reference` + `FixtureReference` ; rendu en sous-requête dans `generate` ; `make-factory` reconnaît les FK (`relations.json`) et propose `reference(...)`.
3. **F44** : tri topologique dans `fixtures:load` (graphe depuis `relations.json`), repli nom de fichier, option `--no-fk-checks`.
4. Doc embarquée (reference.md) et parcours welcome mis à jour.

Chaque ticket : tests + pyright strict + ruff + `mkdocs --strict` verts.

## Conséquences

- Surface d'API élargie (rétro-compatible, additive) :
    - `forge-mvc-fixtures` : `Factory.reference()` et `FixtureReference` (nouveaux, publics) ; `fixtures:load --no-fk-checks` ; `make-factory` scaffolde colonnes réelles et provider « référence ».
    - `forge-mvc-entities` : `column_for_field(field)` public (petit ajout, source unique du mapping colonne, principe 11).
- `forge-mvc-fixtures` acquiert une **dépendance douce** à `forge-mvc-entities` (import optionnel) : cohérent, `make-factory` lit déjà des contrats d'entité ; mode dégradé si absent.
- Un jeu multi-tables relié se charge sans violer les contraintes ; les FK pointent des lignes réelles ; le SQL généré utilise les colonnes de l'entité et reste visible.
- La génération native couvre le cas « seed relié » ; seules les étapes purement métier (import JSON, agrégats) restent hors périmètre (piste callable différée).

## Alternatives écartées

- **F43 par placeholder résolu à la génération** (Ids déterministes assignés au moment de générer le `.sql`).
  Rejetée : fragile face aux `Id` auto-incrémentés réels et à un chargement partiel ; la sous-requête résout contre la base réelle.
- **F45 par parsing du `.sql` d'entité.**
  Écartée au profit de la fonction `column_for_field` du normaliseur : une seule source de vérité du mapping (principe 11), pas d'analyseur SQL fragile.
- **F44 en désactivant toujours les contraintes FK.**
  Rejetée comme défaut : masque les vrais problèmes d'intégrité ; le tri topologique respecte les contraintes, `--no-fk-checks` reste une option explicite pour les cycles.
- **Embarquer un moteur de seed complet (import JSON, agrégats).**
  Hors périmètre : logique métier de l'application ; à évaluer séparément (piste callable).

## Référence

- Charte : `CHARTE_DOC.md` (principe 5, SQL visible ; principe 11, une seule façon officielle).
- [ADR-074](074-fixtures-optin.md) : opt-in fixtures.
- [ADR-075](075-dialect-literal-rendering.md) : rendu de littéral SQL par le dialecte.
- [ADR-076](076-fixtures-factory-generation.md) : génération par classes factory.
- [ADR-069](069-foreign-key-field-type.md) : clé étrangère comme champ d'entité (mapping colonne).
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités (normaliseur, `relations.json`).
