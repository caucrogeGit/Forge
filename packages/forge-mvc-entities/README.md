# forge-mvc-entities

Opt-in Forge qui porte le **moteur d'entités** : la génération et la modélisation
de la couche de données d'une application Forge.

Extrait du cœur (ADR-070) : le cœur reste un noyau web avec la seule couture
runtime d'accès base (`core/database`, contrat `Dialect`), et le moteur d'entités
devient une brique optionnelle, indépendante du SGBD.

## Contenu

- Génération : `make:entity`, `make:relation` (`many_to_one` et `many_to_many`),
  `make:crud`, `make:pivot-crud`.
- Modélisation : normaliseur canonique, validation (`entity:validate`),
  documentation (`entity:doc`), `build:model` / `sync:entity`, génération de
  migrations.
- Provisioning : `db:config`, `db:init`, `db:apply` (workflow « faire vivre les
  entités dans une base »).
- Pivot enrichi : service d'exécution `PivotAdvancedService` et générateur
  `make:pivot-crud` (hérités de `forge-mvc-pivot`, absorbé par cet opt-in).

L'opt-in dépend du contrat `Dialect` exposé par le cœur, jamais d'un backend
concret : le SGBD est fourni séparément par un opt-in de backend
(`forge-mvc-mariadb`, `forge-mvc-sqlite`, `forge-mvc-postgres`, `forge-mvc-mssql`).

## Installation

```bash
pip install forge-mvc-entities
```

`forge new` installe cet opt-in par défaut (ADR-070) : une application qui
modélise des données l'a d'emblée. Un projet purement web peut s'en passer.
