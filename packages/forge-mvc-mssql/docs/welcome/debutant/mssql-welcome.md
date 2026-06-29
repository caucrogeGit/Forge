# Préparer la base

Objectif : premier contact avec le backend **opt-in** `forge-mvc-mssql` (Alpha).

**Ce que vous allez apprendre :** comme le provisioning CLI n'est pas encore câblé, on crée la base et le login à la main, puis Forge prend le relais.

Premier palier du **niveau débutant** de la progression SQL Server.

!!! warning "Alpha : provisioning manuel"
    `forge db:init` ne provisionne pas encore SQL Server.

    On crée donc la base et le login avec les outils SQL Server, puis on utilise `db:apply`.

## Ce que ce palier montre

- créer la base et le login SQL Server ;
- vérifier que le cœur résout le backend.

## 1. Créer base et login

```sql
CREATE DATABASE mon_projet;
CREATE LOGIN mon_projet WITH PASSWORD = 'motdepasse';
USE mon_projet;
CREATE USER mon_projet FOR LOGIN mon_projet;
ALTER ROLE db_owner ADD MEMBER mon_projet;
```

(En conteneur, exécutez ces commandes via `sqlcmd` dans le conteneur SQL Server.)

## 2. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`mssql`) et l'état de la connexion (pilote ODBC compris).

## Après cette étape

[Palier suivant : Appliquer une entité](mssql-apply.md)
