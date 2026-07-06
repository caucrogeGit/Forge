# Valider l'intégration

Objectif : confirmer que SQL Server fonctionne de bout en bout sur votre serveur.

**Ce que vous allez apprendre :** comment vérifier la chaîne complète, puisque l'intégration est à valider (Alpha).

Deuxième palier du **niveau avancé**.

## Démarrer un serveur de test

Un conteneur jetable convient :

```bash
docker run --rm -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Test_1234" \
  -p 1433:1433 mcr.microsoft.com/mssql/server
```

Installez aussi un pilote ODBC (« ODBC Driver 18 for SQL Server »)
et configurez `env/dev`.

## Vérifier la chaîne

1. créer base et login (palier débutant) ;
2. `forge db:apply` (création de tables) ;
3. une migration (`migration:make` puis `migration:apply`) ;
4. lecture/écriture via `core.database.db`.

Si ces quatre étapes passent, l'intégration runtime est bonne sur votre serveur.

## Ce qui n'est pas couvert

- le provisioning par `db:init` (création automatique base + login) ;
- le diff incrémental fin (noms de types SQL Server).

!!! warning "Pilote ODBC indispensable"
    Sans pilote ODBC compatible, `pyodbc` ne peut pas se connecter.

    Vérifiez sa présence avant de tester (le nom se règle via `DB_ODBC_DRIVER`).

!!! note "Remonter les écarts"
    Documenter ce qui marche ou casse sur un vrai serveur aide à faire passer le backend de Alpha à bêta.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
