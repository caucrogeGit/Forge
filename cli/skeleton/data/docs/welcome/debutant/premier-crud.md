# Débutant 2 — Le CRUD

Objectif : lister, consulter, créer, modifier et supprimer vos enregistrements.

À partir de votre entité, Forge génère un CRUD complet :

```bash
forge make:crud
```

Forge crée le modèle, le contrôleur et les vues, et indique la route à monter
dans `mvc/routes.py`.
Montez-la, relancez `python app.py`, puis ouvrez la liste dans le navigateur.

Le SQL reste visible et paramétré : ouvrez le modèle généré pour voir les
requêtes, sans ORM ni magie.

## Pour approfondir

Le CRUD explicite : https://forgemvc.com/docs/forge/features/crud/

## Étape suivante

[Bilan du niveau débutant](bilan.md)
