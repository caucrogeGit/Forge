# forge-mvc-mssql

Backend BDD **Microsoft SQL Server** pour [Forge](https://forgemvc.com), au-dessus
de `pyodbc`.

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il découvre le backend
installé via un entry point. Ce paquet ajoute **SQL Server** à la liste des
choix de SGBD du développeur.

!!! warning "Statut Alpha"
    La logique de dialecte (types, DDL Transact-SQL) est **testée
    unitairement**. L'**intégration avec un serveur SQL Server** (pilote ODBC)
    et le **provisioning par la CLI** (`forge db:init`) restent à
    valider/câbler. À ce stade, créez le schéma manuellement (voir plus bas).

## Installation

```bash
pip install forge-mvc forge-mvc-mssql
```

SQL Server est **client-serveur** : un serveur SQL Server doit être joignable
(installé, en conteneur `mcr.microsoft.com/mssql/server`, ou distant), et un
**pilote ODBC** doit être présent sur la machine cliente (par défaut
« ODBC Driver 18 for SQL Server », surchargeable via `DB_ODBC_DRIVER`).

## Particularités gérées

- **Paramètres** : pyodbc utilise nativement les `?` de Forge (aucune traduction).
- **Identité** : clé primaire auto-incrémentée via `BIGINT IDENTITY(1,1)`.
- **Insertion** : `lastrowid` via `SCOPE_IDENTITY()`.
- **Identifiants** : entre crochets `[...]`.
- **Idempotence** : SQL Server n'a pas `IF NOT EXISTS` ; le dialecte émet des
  formes gardées (`IF OBJECT_ID(...) IS NULL` pour les tables, `IF NOT EXISTS
  (SELECT ... FROM sys.indexes ...)` pour les index).
- **Lignes-dict** : pyodbc ne renvoie pas de dictionnaires ; l'adaptateur
  convertit via `cursor.description`.

## Configuration

Connexion via l'environnement (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`,
`DB_APP_PWD`, et `DB_ODBC_DRIVER` au besoin). Un seul backend BDD par projet.

## Limites connues (Alpha)

- `forge db:init` ne provisionne pas encore SQL Server : créez la base et le
  login/utilisateur à la main, puis appliquez le SQL des entités généré par
  `make:crud`.
- L'introspection de diff compare des noms de types SQL Server : le suivi
  incrémental de schéma peut être imparfait.

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
