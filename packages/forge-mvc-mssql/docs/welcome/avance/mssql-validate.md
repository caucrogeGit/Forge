# Vérifier votre environnement

Objectif : confirmer que SQL Server fonctionne de bout en bout sur votre serveur.

**Ce que vous allez apprendre :** comment vérifier la chaîne complète sur votre environnement.

Deuxième palier du **niveau avancé**.

!!! note "L'intégration est validée en amont"
    La CI de Forge valide le backend contre un vrai SQL Server 2022 : couche BDD et runner de migrations.

    Cette vérification-ci porte sur **votre** environnement : serveur joignable, pilote ODBC présent, configuration `env/` correcte.

## Démarrer un serveur de test

Un conteneur jetable convient :

```bash
docker run --rm -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Test_1234" \
  -p 1433:1433 mcr.microsoft.com/mssql/server
```

Installez aussi un pilote ODBC (« ODBC Driver 18 for SQL Server »)
et configurez `env/dev`.

## Vérifier la chaîne

1. provisionner (`forge db:init --run`, palier débutant) ;
2. `forge db:apply` (création de tables) ;
3. une migration (`migration:make` puis `migration:apply`) ;
4. lecture/écriture via `core.database.db`.

Si ces quatre étapes passent, la chaîne est bonne sur votre environnement.

!!! warning "Pilote ODBC indispensable"
    Sans pilote ODBC compatible, `pyodbc` ne peut pas se connecter.

    Vérifiez sa présence avant de tester (le nom se règle via `DB_ODBC_DRIVER`).

## Après cette étape

[Bilan du niveau avancé](bilan.md)
