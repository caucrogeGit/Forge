# Débutant 1 — Votre première entité

Objectif : modéliser une donnée de votre application.

Une entité Forge est décrite par un contrat JSON (la source de vérité), à partir
duquel Forge génère le SQL et le modèle Python.

## Générer une entité

```bash
forge make:entity
```

Renseignez le nom et les champs.
Forge crée le dossier de l'entité sous `mvc/entities/` (contrat JSON, SQL,
modèle). Ajustez les champs dans le contrat, puis appliquez le schéma à la base :

```bash
forge db:apply
```

## Pour approfondir

Le format des contrats d'entité :
https://forgemvc.com/docs/forge/entities/entity-schema/

## Étape suivante

[Suivant : le CRUD](premier-crud.md)
