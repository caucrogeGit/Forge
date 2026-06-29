# Installation de forge-mvc-postgres

Objectif : installer le backend PostgreSQL et préparer l'accès au serveur.

Le parcours qui suit montre, en trois niveaux, comment préparer la base à la main (Alpha), appliquer un schéma, gérer les migrations, puis comprendre le dialecte et le statut.

!!! warning "Statut Alpha"
    Le provisioning par `db:init` n'est pas encore câblé pour PostgreSQL.

    Ce parcours crée la base et le rôle manuellement, puis utilise `db:apply` / `migration:*`.

## Pré-requis : un serveur PostgreSQL

PostgreSQL est client-serveur : il faut un serveur joignable (local, conteneur Docker, ou distant).

## Installer le paquet

```bash
pip install --pre forge-mvc-postgres
```

Le paquet dépend du cœur `forge-mvc` et de `psycopg` (v3).

## Configurer l'environnement

Dans `env/dev` : `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`, `DB_APP_PWD`.

## Vérifier

```python
from importlib.metadata import entry_points
print("postgres" in {e.name for e in entry_points(group="forge_mvc.db_backend")})
```

`True` signifie que le cœur peut découvrir le backend.

!!! note "Un seul backend par projet"
    Si un autre backend est installé, fixez `DB_BACKEND=postgres`.

## Après cette étape

[Niveau débutant : Préparer la base](debutant/postgres-welcome.md)
