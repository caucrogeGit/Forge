# ADR-075 : Rendu de littéraux SQL par le contrat Dialect

## Statut

Acceptée.
Décision d'architecture ; relève du mainteneur.

## Date

2026-07-11

## Contexte

Le cœur de Forge est agnostique du SGBD : les backends sont des opt-ins exclusifs, découverts par entry point, et exposent un contrat `Dialect` (ADR-054).
Ce contrat couvre aujourd'hui la **DDL** : mapping des types Forge vers les types de colonne, construction du `CREATE TABLE`, contraintes, et `quote_identifier` (backticks MariaDB, guillemets SQLite/PostgreSQL, crochets SQL Server).

Il ne couvre **pas** le rendu d'une **valeur littérale** : transformer une valeur Python (`'Lyon'`, `True`, une date) en son écriture SQL correcte pour le backend visé.

Deux constats motivent l'ajout.

**Un besoin nouveau.** L'opt-in `forge-mvc-fixtures` (ADR-074) doit pouvoir **générer** des fichiers `mvc/fixtures/*.sql`.
Un fichier `.sql` est du texte statique : il ne transporte pas de paramètres, les valeurs y sont donc des **littéraux gravés dans le SQL**.
Or ces littéraux diffèrent selon le backend : booléen `1`/`0` (MariaDB, SQLite, SQL Server) contre `TRUE`/`FALSE` (PostgreSQL), chaîne `'x'` contre `N'x'` (SQL Server, Unicode), formes de dates, quoting d'identifiants.
Comme un projet a **un seul** backend (exclusif, ADR-054), générer pour ce backend est le choix naturel, et cela exige de savoir rendre un littéral dans son dialecte.

**Une duplication existante, dialecte-naïve.** Le moteur d'entités porte déjà un rendu de littéral, `forge_mvc_entities.make_entity.sql_default_literal`, utilisé pour les clauses `DEFAULT` de la DDL générée.
Il est **dialecte-naïf** : booléen toujours `1`/`0`, dates via `str()`, aucune connaissance du backend.
C'est un rendu de littéral qui vit **hors** du contrat `Dialect` et qui contient un bug de portabilité latent (le `DEFAULT` d'un booléen ou d'une date est faux en PostgreSQL).

Le rendu d'un littéral SQL est un **trait dialectal générique**, utile à tout générateur qui émet de la DML ou des valeurs par défaut, pas seulement aux fixtures.
Il a donc sa place dans le contrat `Dialect` du cœur, pas dans un opt-in.

## Décision

Étendre le contrat `Dialect` (cœur, `core/database/backend.py`) d'une méthode de rendu de littéral :

```python
def render_literal(self, value: object) -> str:
    """Rend une valeur Python comme littéral SQL de ce dialecte."""
```

Couverture (types Python correspondant aux types Forge) :

- `None` vers `NULL` ;
- `bool` vers le booléen du dialecte (`1`/`0` ou `TRUE`/`FALSE`) ;
- `int` vers un entier décimal ;
- `float` et `Decimal` vers un numérique ;
- `str` vers une chaîne quotée et échappée selon le dialecte (`''` doublé partout ; préfixe `N'...'` en SQL Server) ;
- `date` et `datetime` vers le littéral de date du dialecte ;
- type non couvert vers une **erreur explicite** (jamais un `str()` silencieux).

Le quoting des identifiants reste `quote_identifier`, déjà au contrat.

**Chaque backend implémente `render_literal`** avec ses règles : `forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres`, `forge-mvc-mssql`.

**Consolidation (principe 11).** `sql_default_literal` du moteur d'entités est réécrit **au-dessus** de `dialect.render_literal` : il ne fait plus que lire `field["default"]` puis déléguer.
Le rendu de littéral devient ainsi la **seule façon officielle**, dialecte-correcte, et le bug de portabilité des `DEFAULT` disparaît.

### Périmètre et sécurité (non négociable)

`render_literal` sert à **générer des artefacts SQL relus hors requête** : fichiers de fixtures, clauses `DEFAULT` de DDL, SQL de modèle.
Il **n'est pas** un constructeur de requête à l'exécution.

La DML applicative continue d'utiliser des **requêtes paramétrées** (placeholders de `core.database.db`), inchangées.
`render_literal` ne doit **jamais** servir à interpoler une entrée de requête non fiable dans une requête vivante : ce serait une porte d'injection SQL (principe 7, sécuriser par défaut).
Son rôle est de produire du SQL **visible et relu** (principe 5), à partir de données maîtrisées par le développeur (une recette de fixtures, une valeur par défaut d'entité).

## Mise en œuvre (phasage)

Tickets distincts, dans l'ordre :

1. Ajouter `render_literal` au `Protocol` `Dialect` (cœur) et son garde-fou de contrat.
2. Implémenter `render_literal` dans les quatre backends, avec les règles propres à chaque dialecte et leurs tests unitaires.
3. Consolider `sql_default_literal` (moteur d'entités) sur `dialect.render_literal` ; corriger le rendu des `DEFAULT` booléens et dates.
4. (Débloqué, hors de cet ADR) `forge fixtures:generate` s'appuie sur `render_literal` pour émettre des fixtures `.sql` correctes pour le backend installé.

## Conséquences

- Le contrat `Dialect` gagne un concern **DML/littéral** à côté de son concern DDL.
- Ajouter une méthode au `Protocol` impose son implémentation dans les **quatre** backends (PostgreSQL et SQL Server compris).
- Un rendu de littéral dialecte-naïf et dupliqué disparaît (moteur d'entités) ; un bug de portabilité des `DEFAULT` (booléens, dates en PostgreSQL) est corrigé au passage.
- La génération de fixtures native au backend (ADR-074) est débloquée, sans que l'opt-in fixtures ne connaisse les dialectes : il passe par le contrat.
- La posture anti-injection est préservée : le rendu de littéral est cantonné à la génération d'artefacts relus, la DML d'exécution reste paramétrée.

## Alternatives écartées

- **Garder le rendu de littéral dans chaque générateur** (fixtures, entités).
  Rejetée : duplication, rendu dialecte-naïf, contradiction avec le principe 11.
- **Rendre un SQL ANSI portable sans passer par le dialecte.**
  Rejetée : faux pour les booléens, les dates et les identifiants réservés sur certains backends ; n'exploite pas le fait que le backend est exclusif et déjà connu.
- **Des fixtures paramétrées (valeurs hors du fichier).**
  Rejetée : un fichier `.sql` ne transporte pas de paramètres ; cela casserait le format SQL simple, visible et relu (principe 5).
- **Exposer `render_literal` comme constructeur de requête général.**
  Rejetée : rouvrirait la voie à l'injection SQL ; la DML d'exécution doit rester paramétrée (principe 7).

## Référence

- Charte : `CHARTE_DOC.md` (principe 5, SQL visible ; principe 7, sécuriser par défaut ; principe 11, une seule façon officielle).
- [ADR-054](054-database-backend-optins.md) : cœur agnostique, backends exclusifs, contrat `Dialect`.
- [ADR-070](070-entities-engine-extraction.md) : moteur d'entités (porte `sql_default_literal`, consolidé ici).
- [ADR-074](074-fixtures-optin.md) : opt-in fixtures, consommateur de `render_literal` pour `fixtures:generate`.
- `core/database/backend.py` : contrat `Dialect` à étendre.
