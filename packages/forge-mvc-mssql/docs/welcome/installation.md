# Installation de forge-mvc-mssql

Objectif : installer le backend SQL Server et préparer l'accès au serveur.

Le parcours qui suit montre, en trois niveaux, comment préparer la base à la main (Alpha), appliquer un schéma, gérer les migrations, puis comprendre le dialecte et le statut.

!!! warning "Statut Alpha"
    Le provisioning par `db:init` n'est pas encore câblé pour SQL Server.

    Ce parcours crée la base et le login manuellement, puis utilise `db:apply` / `migration:*`.

## Pré-requis : serveur + pilote ODBC

SQL Server est client-serveur : il faut un serveur joignable, et un **pilote ODBC** sur la machine cliente (par défaut « ODBC Driver 18 for SQL Server »).

## Installer le paquet

```bash
pip install --pre forge-mvc-mssql
```

Le paquet dépend du cœur `forge-mvc` et de `pyodbc`.

## Configurer l'environnement

Dans `env/dev` : `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`, `DB_APP_PWD`, et au besoin `DB_ODBC_DRIVER`.

## Vérifier

```python
from importlib.metadata import entry_points
print("mssql" in {e.name for e in entry_points(group="forge_mvc.db_backend")})
```

`True` signifie que le cœur peut découvrir le backend.

!!! note "Un seul backend par projet"
    Si un autre backend est installé, fixez `DB_BACKEND=mssql`.

## Après cette étape

[Niveau débutant : Préparer la base](debutant/mssql-welcome.md)
